"""CLI entry points; data inspection does not import the ML stack."""

import argparse
import json
from pathlib import Path

from .data import DataError, import_wide, load_dataset, save_dataset, validate


def main() -> None:
    parser = argparse.ArgumentParser(description="CV-JD GNN: du lieu, huan luyen, danh gia va du doan bang Python")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("make-demo", help="Tao du lieu gia lap nho de thu luong chay")
    demo.add_argument("--output", type=Path, required=True)
    demo.add_argument("--cvs", type=int, default=60)
    demo.add_argument("--seed", type=int, default=42)
    bridge = commands.add_parser("import-wide", help="Chuyen CSV tong hop cua nhom sang 3 bang chuan")
    bridge.add_argument("--input", type=Path, required=True)
    bridge.add_argument("--output", type=Path, required=True)
    bridge.add_argument("--label-column", default="human_label")
    bridge.add_argument("--label-source", choices=["human", "heuristic"], default="human")
    bridge.add_argument("--seed", type=int, default=42)
    prepare = commands.add_parser("prepare", help="Chuan hoa 3 bang; chia theo CV neu toan bo split de trong")
    prepare.add_argument("--data", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--seed", type=int, default=42)
    inspect = commands.add_parser("validate", help="Kiem tra schema, nhan va ro ri CV")
    inspect.add_argument("--data", type=Path, required=True)
    inspect.add_argument("--for-training", action="store_true")
    inspect.add_argument("--allow-weak-labels", action="store_true")
    training = commands.add_parser("train", help="Huan luyen GNN va doi chieu baseline")
    training.add_argument("--data", type=Path, required=True)
    training.add_argument("--output", type=Path, required=True)
    training.add_argument("--config", type=Path)
    training.add_argument("--epochs", type=int)
    training.add_argument("--allow-weak-labels", action="store_true")
    evaluation = commands.add_parser("evaluate", help="Tai checkpoint va danh gia lai test cua run")
    evaluation.add_argument("--run", type=Path, required=True)
    evaluation.add_argument("--data", type=Path, required=True)
    prediction = commands.add_parser("predict", help="Xep hang JD da biet cho mot CV moi")
    prediction.add_argument("--run", type=Path, required=True)
    source = prediction.add_mutually_exclusive_group(required=True)
    source.add_argument("--cv-json", type=Path)
    source.add_argument("--cv-text", type=Path)
    prediction.add_argument("--top-k", type=int, default=5)
    prediction.add_argument("--output", type=Path)
    web = commands.add_parser("web", help="Mo giao dien web tren localhost")
    web.add_argument("--runs-dir", type=Path, default=Path("runs"))
    web.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        if args.command == "make-demo":
            from .demo import make_demo
            result = make_demo(args.output, args.cvs, args.seed)
        elif args.command == "import-wide":
            result = import_wide(args.input, args.output, label_column=args.label_column,
                                 label_source=args.label_source, seed=args.seed)
        elif args.command == "prepare":
            dataset = load_dataset(args.data, split_seed=args.seed)
            save_dataset(dataset, args.output)
            result = validate(dataset)
        elif args.command == "validate":
            result = validate(load_dataset(args.data), for_training=args.for_training, allow_weak=args.allow_weak_labels)
        elif args.command == "train":
            from .training import TrainConfig, train
            config = TrainConfig.load(args.config)
            if args.epochs is not None:
                config.epochs = args.epochs
            metrics = train(args.data, args.output, config, allow_weak=args.allow_weak_labels)
            result = {"run": str(args.output), "dataset_kind": metrics["dataset_kind"],
                      "best_epoch": metrics["best_epoch"], "test_macro_f1": metrics["gnn"]["test"]["macro_f1"],
                      "metrics_file": str(args.output / "metrics.json"), "warnings": metrics["warnings"]}
        elif args.command == "evaluate":
            from .predict import evaluate
            result = evaluate(args.run, args.data)
        elif args.command == "web":
            from .web import serve
            serve(args.runs_dir, args.port)
            return
        else:
            from .predict import predict
            result = predict(args.run, cv_json=args.cv_json, cv_text=args.cv_text, top_k=args.top_k, output=args.output)
    except (DataError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
