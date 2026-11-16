import json
from pathlib import Path

from ._torch import torch

from .data import LABELS, DataError, Document, extract_known_skills, load_dataset, normalize_skills, write_csv
from .features import TextEncoder
from .graph import Context, Graph, add_queries
from .model import CVJDModel


def load_run(folder: Path):
    names = ("run.json", "model.pt", "text_encoder.json", "graph_metadata.json", "graph_context.pt", "job_catalog.json")
    if any(not (folder / name).is_file() for name in names):
        raise DataError(f"{folder}: thieu artifact. Hay chay train thanh cong truoc.")
    run = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    torch.set_num_threads(run["config"].get("torch_threads", 2))
    checkpoint = torch.load(folder / "model.pt", map_location="cpu", weights_only=True)
    if checkpoint.get("format_version") != 1:
        raise DataError("Checkpoint version chua duoc ho tro")
    model = CVJDModel(**checkpoint["model_args"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    encoder = TextEncoder.load(folder / "text_encoder.json")
    metadata = json.loads((folder / "graph_metadata.json").read_text(encoding="utf-8"))
    tensors = torch.load(folder / "graph_context.pt", map_location="cpu", weights_only=True)
    graph = Graph(tensors["x_dict"], tensors["edge_index_dict"])
    context = Context(graph, metadata["cv_ids"], metadata["job_ids"], metadata["skill_names"])
    jobs = json.loads((folder / "job_catalog.json").read_text(encoding="utf-8"))
    return model, encoder, context, jobs, run


def predict(folder: Path, *, cv_json: Path | None = None, cv_text: Path | None = None,
            top_k: int = 5, output: Path | None = None) -> dict:
    if output is not None and output.exists():
        raise DataError(f"File dau ra da ton tai: {output}; chon ten moi")
    if cv_json is not None:
        record = json.loads(cv_json.read_text(encoding="utf-8-sig"))
    elif cv_text is not None:
        record = {"cv_text": cv_text.read_text(encoding="utf-8-sig")}
    else:
        raise DataError("Can --cv-json hoac --cv-text")
    result = predict_record(folder, record, top_k=top_k)
    if output is not None:
        write_csv(output, list(result["ranked_jobs"][0]), result["ranked_jobs"])
    return result


def predict_record(folder: Path, record: dict, *, top_k: int = 5, loaded_run=None) -> dict:
    """Shared inference for CLI and local web; CV contents stay in memory."""
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise DataError("Số kết quả phải là số nguyên lớn hơn 0.")
    if not isinstance(record, dict):
        raise DataError("CV JSON phải là một object có trường cv_text.")
    text, supplied = record.get("cv_text", ""), record.get("cv_skills")
    if not isinstance(text, str) or (supplied is not None and not isinstance(supplied, (list, str))):
        raise DataError("cv_text phải là văn bản; cv_skills là danh sách hoặc chuỗi ngăn cách bằng dấu ;.")
    if isinstance(supplied, list) and any(not isinstance(s, str) for s in supplied):
        raise DataError("Mỗi kỹ năng phải là một chuỗi văn bản.")
    if not text.strip():
        raise DataError("Bạn chưa nhập nội dung CV.")
    model, encoder, context, jobs, run = loaded_run if loaded_run is not None else load_run(folder)
    skills = normalize_skills(supplied) if supplied is not None else extract_known_skills(text, context.skill_names)
    query = Document("__prediction_query__", text, skills)
    extended = add_queries(context, [query], encoder)
    cv_index = torch.full((len(context.job_ids),), len(context.cv_ids), dtype=torch.long)
    jd_index = torch.arange(len(context.job_ids), dtype=torch.long)
    with torch.no_grad():
        probabilities = model(extended.graph, cv_index, jd_index).softmax(-1)
    records = []
    for jd_id, prob in zip(context.job_ids, probabilities):
        required = set(jobs[jd_id]["skills"])
        records.append({"jd_id": jd_id, "jd_title": jobs[jd_id]["title"],
                        "ranking_score": round(float(100 * (0.5 * prob[1] + prob[2])), 4),
                        "predicted_label": LABELS[int(prob.argmax())],
                        **{f"p_{label}": float(prob[i]) for i, label in enumerate(LABELS)},
                        "matched_skills": "; ".join(sorted(required.intersection(skills))),
                        "missing_skills": "; ".join(sorted(required.difference(skills)))})
    records.sort(key=lambda row: (-row["ranking_score"], row["jd_id"]))
    records = records[:top_k]
    return {"dataset_kind": run["dataset"]["dataset_kind"], "ranked_jobs": records,
            "recognized_skills": list(skills), "unknown_graph_skills": sorted(set(skills) - set(context.skill_names)),
            "note": "Diem xep hang cua mo hinh, khong phai xac suat duoc tuyen. Ky nang trung/thieu la doi chieu danh sach, khong phai giai thich nhan qua cua GNN.",
            "training_warnings": run["dataset"]["warnings"]}


def evaluate(folder: Path, data_dir: Path) -> dict:
    from .training import fingerprint, inference_metrics

    model, encoder, context, _, run = load_run(folder)
    if fingerprint(data_dir) != run["data_sha256"]:
        raise DataError("Dataset da thay doi so voi run. Tao run moi de danh gia co the tai lap.")
    dataset = load_dataset(data_dir)
    queries = [dataset.cvs[k] for k in dataset.cv_ids("test")]
    extended = add_queries(context, queries, encoder)
    metrics, _ = inference_metrics(model, extended, dataset.labelled_pairs("test"), "cpu")
    return {"dataset_kind": run["dataset"]["dataset_kind"], "test": metrics, "warnings": run["dataset"]["warnings"]}
