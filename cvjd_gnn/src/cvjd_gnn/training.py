from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path

from ._torch import torch
from torch.nn import functional as F

from .data import LABELS, DataError, ensure_empty_output, load_dataset, validate, write_csv, write_json
from .features import TextEncoder
from .graph import add_queries, build_context, pair_tensors
from .metrics import baselines, classification_metrics
from .model import CVJDModel


@dataclass
class TrainConfig:
    seed: int = 42
    epochs: int = 60
    patience: int = 12
    learning_rate: float = 0.003
    weight_decay: float = 0.0001
    hidden_channels: int = 64
    layers: int = 2
    dropout: float = 0.2
    max_features: int = 1024
    class_weighted_loss: bool = True
    device: str = "cpu"
    torch_threads: int = 2

    @classmethod
    def load(cls, path: Path | None) -> "TrainConfig":
        payload = json.loads(path.read_text(encoding="utf-8-sig")) if path else {}
        unknown = set(payload) - {f.name for f in fields(cls)}
        if unknown:
            raise DataError(f"Config co khoa khong hop le: {sorted(unknown)}")
        result = cls(**payload)
        result.check()
        return result

    def check(self):
        for key in ("epochs", "patience", "hidden_channels", "layers", "max_features", "torch_threads"):
            value = getattr(self, key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise DataError(f"{key} phai la so nguyen duong")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool) or not 0 <= self.seed < 2**32:
            raise DataError("seed phai la so nguyen trong [0, 2^32)")
        for key in ("learning_rate", "weight_decay", "dropout"):
            if not isinstance(getattr(self, key), (int, float)) or not math.isfinite(getattr(self, key)):
                raise DataError(f"{key} phai la so huu han")
        if self.learning_rate <= 0 or self.weight_decay < 0 or not 0 <= self.dropout < 1:
            raise DataError("learning_rate > 0, weight_decay >= 0, va 0 <= dropout < 1")
        if not isinstance(self.class_weighted_loss, bool):
            raise DataError("class_weighted_loss phai la true/false")
        if self.device not in {"cpu", "cuda"}:
            raise DataError("device phai la cpu hoac cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise DataError("CUDA khong san sang. Dung device=cpu hoac cai ban PyTorch CUDA phu hop.")


def fingerprint(folder: Path) -> dict[str, str]:
    result = {}
    for name in ("cvs.csv", "jobs.csv", "pairs.csv", "manifest.json"):
        path = folder / name
        if path.exists():
            with path.open("rb") as stream:
                result[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    return result


def inference_metrics(model, context, pairs, device: str):
    model.eval()
    ci, ji, labels = pair_tensors(context, pairs)
    with torch.no_grad():
        logits = model(context.graph.to(device), ci.to(device), ji.to(device))
        loss = float(F.cross_entropy(logits, labels.to(device)).item())
        probabilities = logits.softmax(-1).cpu()
    metrics = classification_metrics(labels.tolist(), probabilities.argmax(-1).tolist())
    metrics["loss"] = loss
    return metrics, probabilities


def train(data_dir: Path, output: Path, config: TrainConfig, *, allow_weak: bool = False) -> dict:
    config.check()
    source_fingerprint = fingerprint(data_dir)
    dataset = load_dataset(data_dir)
    summary = validate(dataset, for_training=True, allow_weak=allow_weak)
    if output.exists() and any(output.iterdir()):
        raise DataError(f"Run da ton tai: {output}. Hay chon --output moi.")
    random.seed(config.seed)
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.seed)
    torch.set_num_threads(config.torch_threads)
    torch.use_deterministic_algorithms(True, warn_only=True)
    encoder = TextEncoder(config.max_features)
    context = build_context(dataset, encoder)
    val_context = add_queries(context, [dataset.cvs[k] for k in dataset.cv_ids("validation")], encoder)
    train_pairs = dataset.labelled_pairs("train")
    val_pairs = dataset.labelled_pairs("validation")
    ci, ji, labels = (tensor.to(config.device) for tensor in pair_tensors(context, train_pairs))
    model_args = {"input_channels": encoder.dimension, "hidden_channels": config.hidden_channels,
                  "layers": config.layers, "dropout": config.dropout}
    model = CVJDModel(**model_args).to(config.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    weights = None
    if config.class_weighted_loss:
        counts = torch.bincount(labels, minlength=3).float()
        weights = len(labels) / (3 * counts)
    ensure_empty_output(output)
    best_f1, best_loss, best_epoch, best_state = -1.0, float("inf"), 0, None
    history = []
    train_graph = context.graph.clone().to(config.device)
    print(f"Dataset: {summary['dataset_kind']}; train pairs: {len(train_pairs)}; device: {config.device}")
    for warning in summary["warnings"]:
        print(f"NOTE: {warning}")
    for epoch in range(1, config.epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(train_graph, ci, ji), labels, weight=weights)
        if not torch.isfinite(loss):
            raise DataError("Loss khong huu han; kiem tra du lieu va learning_rate")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()
        val_metrics, _ = inference_metrics(model, val_context, val_pairs, config.device)
        history.append({"epoch": epoch, "train_loss": float(loss.item()),
                        "validation_loss": val_metrics["loss"], "validation_macro_f1": val_metrics["macro_f1"]})
        f1, val_loss = val_metrics["macro_f1"], val_metrics["loss"]
        if f1 > best_f1 or (f1 == best_f1 and val_loss < best_loss):
            best_f1, best_loss, best_epoch = f1, val_loss, epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        if epoch == 1 or epoch % 10 == 0:
            print(f"Epoch {epoch}: loss={loss.item():.4f}; val macro-F1={f1:.4f}")
        if epoch - best_epoch >= config.patience:
            break
    model.load_state_dict(best_state)
    validation_metrics, _ = inference_metrics(model, val_context, val_pairs, config.device)
    # The test labels are used only after model selection has finished.
    test_context = add_queries(context, [dataset.cvs[k] for k in dataset.cv_ids("test")], encoder)
    test_pairs = dataset.labelled_pairs("test")
    test_metrics, probabilities = inference_metrics(model, test_context, test_pairs, config.device)
    metrics = {"dataset_kind": summary["dataset_kind"], "label_sources": {
        split: info["label_sources"] for split, info in summary["splits"].items()},
        "best_epoch": best_epoch, "epochs_run": len(history),
        "gnn": {"validation": validation_metrics, "test": test_metrics},
        "baselines": baselines(dataset, encoder, config.seed), "warnings": summary["warnings"]}
    if fingerprint(data_dir) != source_fingerprint:
        raise DataError("Dataset thay doi trong luc huan luyen. Chay lai voi phien ban du lieu co dinh.")
    encoder.save(output / "text_encoder.json")
    torch.save({"format_version": 1, "model_args": model_args, "state_dict": best_state}, output / "model.pt")
    base = context.graph.to("cpu")
    torch.save({"x_dict": base.x_dict, "edge_index_dict": base.edge_index_dict}, output / "graph_context.pt")
    write_json(output / "graph_metadata.json", {"cv_ids": context.cv_ids, "job_ids": context.job_ids,
                                                "skill_names": context.skill_names})
    # No full CV text is included in inference artifacts.
    write_json(output / "job_catalog.json", {key: asdict(dataset.jobs[key]) for key in context.job_ids})
    write_json(output / "metrics.json", metrics)
    write_json(output / "run.json", {"format_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
                                    "config": asdict(config), "dataset": summary, "data_sha256": source_fingerprint,
                                    "allow_weak_labels": allow_weak,
                                    "protocol": "inductive_new_cv_known_job_catalog; query-to-context edges disabled",
                                    "versions": {"torch": str(torch.__version__), "graphsage": "native_pytorch_mean_v1"}})
    write_csv(output / "history.csv", list(history[0]), history)
    predictions = [{"cv_id": pair.cv_id, "jd_id": pair.jd_id, "truth": LABELS[pair.label],
                    "prediction": LABELS[int(prob.argmax())], "label_source": pair.label_source,
                    **{f"p_{label}": float(prob[i]) for i, label in enumerate(LABELS)}}
                   for pair, prob in zip(test_pairs, probabilities)]
    write_csv(output / "test_predictions.csv", list(predictions[0]), predictions)
    return metrics
