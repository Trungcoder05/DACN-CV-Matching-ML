"""Data contracts, strict validation, and a bridge from the team's wide CSV."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

LABELS = ("low", "medium", "high")
SPLITS = ("train", "validation", "test")
LABEL_ALIASES = {"thấp": 0, "trung bình": 1, "cao": 2, "0": 0, "1": 1, "2": 2,
                 **{name: i for i, name in enumerate(LABELS)}}
SKILL_ALIASES = {"js": "javascript", "reactjs": "react", "react.js": "react", "nodejs": "node.js",
                 "node js": "node.js", "dotnet": ".net", "c sharp": "c#", "csharp": "c#",
                 "c plus plus": "c++", "cpp": "c++", "postgres": "postgresql", "powerbi": "power bi",
                 "ml": "machine learning", "dl": "deep learning", "restful api": "rest api"}


class DataError(ValueError):
    """An actionable dataset or configuration problem."""


def normalize_skills(value: str | list[str]) -> tuple[str, ...]:
    parts = value.split(";") if isinstance(value, str) else value
    clean = {" ".join(p.casefold().split()) for p in parts if p.strip()}
    return tuple(sorted({SKILL_ALIASES.get(p, p) for p in clean}))


def text_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.casefold().split()).encode("utf-8")).hexdigest()


def parse_label(value: str) -> int | None:
    if not value.strip():
        return None
    try:
        return LABEL_ALIASES[value.strip().casefold()]
    except KeyError as exc:
        raise DataError(f"Nhan '{value}' khong hop le. Dung low/medium/high, 0/1/2 hoac Thấp/Trung bình/Cao.") from exc


def read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    csv.field_size_limit(50_000_000)
    if not path.is_file():
        raise DataError(f"Khong tim thay {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise DataError(f"{path.name}: thieu cot {sorted(missing)}")
        rows = list(reader)
    for i, row in enumerate(rows, 2):
        if None in row or any(v is None for v in row.values()):
            raise DataError(f"{path.name}: ban ghi {i} sai so cot CSV")
    if not rows:
        raise DataError(f"{path.name}: chua co du lieu")
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    skills: tuple[str, ...]
    title: str = ""
    source: str = ""


@dataclass(frozen=True)
class Pair:
    cv_id: str
    jd_id: str
    label: int | None
    label_source: str
    split: str


@dataclass
class Dataset:
    cvs: dict[str, Document]
    jobs: dict[str, Document]
    pairs: list[Pair]
    manifest: dict

    def cv_ids(self, split: str) -> list[str]:
        return sorted({p.cv_id for p in self.pairs if p.split == split})

    def labelled_pairs(self, split: str) -> list[Pair]:
        return [p for p in self.pairs if p.split == split and p.label is not None]


def load_dataset(folder: Path, *, split_seed: int | None = None) -> Dataset:
    cvs, jobs = {}, {}
    for filename, prefix, destination in (("cvs.csv", "cv", cvs), ("jobs.csv", "jd", jobs)):
        for row in read_csv(folder / filename, (f"{prefix}_id", f"{prefix}_text", f"{prefix}_skills")):
            key, text = row[f"{prefix}_id"].strip(), row[f"{prefix}_text"].strip()
            if not key or not text:
                raise DataError(f"{filename}: id va text phai co noi dung")
            if key in destination:
                raise DataError(f"{filename}: id bi lap {key}")
            destination[key] = Document(key, text, normalize_skills(row[f"{prefix}_skills"]),
                                        row.get("jd_title", "").strip(), row.get("source", "").strip())
    pairs = []
    for row in read_csv(folder / "pairs.csv", ("cv_id", "jd_id", "label", "label_source", "split")):
        pairs.append(Pair(row["cv_id"].strip(), row["jd_id"].strip(), parse_label(row["label"]),
                          row["label_source"].strip().casefold(), row["split"].strip().casefold()))
    manifest_file = folder / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8-sig")) if manifest_file.exists() else {"dataset_kind": "unspecified"}
    if not isinstance(manifest, dict):
        raise DataError("manifest.json phai la JSON object")
    if split_seed is not None and not any(pair.split for pair in pairs):
        mapping = assign_splits({key: {"cv_text": document.text} for key, document in cvs.items()}, split_seed)
        pairs = [replace(pair, split=mapping[pair.cv_id]) if pair.cv_id in mapping else pair for pair in pairs]
        manifest = {**manifest, "split_seed": split_seed}
    dataset = Dataset(cvs, jobs, pairs, manifest)
    validate(dataset)
    return dataset


def save_dataset(dataset: Dataset, folder: Path) -> None:
    validate(dataset)
    ensure_empty_output(folder)
    write_csv(folder / "cvs.csv", ["cv_id", "cv_text", "cv_skills", "source"], [
        {"cv_id": d.id, "cv_text": d.text, "cv_skills": "; ".join(d.skills), "source": d.source}
        for d in dataset.cvs.values()])
    write_csv(folder / "jobs.csv", ["jd_id", "jd_title", "jd_text", "jd_skills", "source"], [
        {"jd_id": d.id, "jd_title": d.title, "jd_text": d.text, "jd_skills": "; ".join(d.skills), "source": d.source}
        for d in dataset.jobs.values()])
    write_csv(folder / "pairs.csv", ["cv_id", "jd_id", "label", "label_source", "split"], [
        {"cv_id": p.cv_id, "jd_id": p.jd_id, "label": LABELS[p.label] if p.label is not None else "",
         "label_source": p.label_source, "split": p.split} for p in dataset.pairs])
    write_json(folder / "manifest.json", dataset.manifest)


def validate(dataset: Dataset, *, for_training: bool = False, allow_weak: bool = False) -> dict:
    if not dataset.cvs or not dataset.jobs or not dataset.pairs:
        raise DataError("Dataset can CV, JD va cac cap lien ket")
    for collection in (dataset.cvs, dataset.jobs):
        for key, document in collection.items():
            if not key.strip() or key != document.id or not document.text.strip():
                raise DataError("ID va noi dung CV/JD khong duoc rong hoac mau thuan")
    seen = set()
    cv_splits, content_splits = defaultdict(set), defaultdict(set)
    for pair in dataset.pairs:
        if pair.cv_id not in dataset.cvs or pair.jd_id not in dataset.jobs:
            raise DataError(f"Cap {pair.cv_id}/{pair.jd_id}: tham chieu id khong ton tai")
        key = (pair.cv_id, pair.jd_id)
        if key in seen:
            raise DataError(f"Cap CV-JD bi lap: {key}")
        seen.add(key)
        if pair.split not in SPLITS:
            raise DataError(f"Split '{pair.split}' khong hop le; can train/validation/test")
        if pair.label is not None and pair.label_source not in {"human", "heuristic", "synthetic"}:
            raise DataError(f"{key}: nhan co gia tri nhung label_source khong hop le")
        if pair.label_source == "synthetic" and dataset.manifest.get("dataset_kind") != "synthetic_demo":
            raise DataError("Nhan synthetic chi danh cho manifest dataset_kind=synthetic_demo")
        cv_splits[pair.cv_id].add(pair.split)
        content_splits[text_hash(dataset.cvs[pair.cv_id].text)].add(pair.split)
    if any(len(s) > 1 for s in cv_splits.values()):
        raise DataError("Ro ri du lieu: cung cv_id xuat hien o nhieu split")
    if any(len(s) > 1 for s in content_splits.values()):
        raise DataError("Ro ri du lieu: noi dung CV trung sau chuan hoa o nhieu split")
    summary = {"dataset_kind": dataset.manifest.get("dataset_kind", "unspecified"),
               "cvs": len(dataset.cvs), "jobs": len(dataset.jobs), "pairs": len(dataset.pairs),
               "cv_text_groups": len(content_splits), "splits": {}, "warnings": []}
    for split in SPLITS:
        labelled = dataset.labelled_pairs(split)
        summary["splits"][split] = {"cvs": len(dataset.cv_ids(split)), "labelled_pairs": len(labelled),
                                    "labels": dict(Counter(LABELS[p.label] for p in labelled)),
                                    "label_sources": dict(Counter(p.label_source for p in labelled))}
        if for_training and not labelled:
            raise DataError(f"Tap {split} chua co nhan. Gan nhan human hoac dung demo de thu pipeline.")
        if for_training and not allow_weak and any(p.label_source == "heuristic" for p in labelled):
            raise DataError("Co nhan heuristic. Chi thu nghiem nhan yeu khi them --allow-weak-labels.")
    if for_training and {p.label for p in dataset.labelled_pairs("train")} != {0, 1, 2}:
        raise DataError("Tap train can co ca 3 lop low, medium, high")
    if any(not d.source for d in [*dataset.cvs.values(), *dataset.jobs.values()]):
        summary["warnings"].append("Mot so CV/JD chua co source; can xac minh nguon truoc bao cao.")
    if len(dataset.jobs) < 30:
        summary["warnings"].append("Danh muc JD con nho; khong suy rong ket qua cho thi truong tuyen dung.")
    summary["warnings"].append("Giao thuc: CV moi, danh muc JD da biet. Chua do tong quat hoa sang JD moi.")
    if any(p.label_source == "heuristic" for p in dataset.pairs):
        summary["warnings"].append("Nhan heuristic do quy tac tao; khong phai danh gia chuyen gia.")
    if summary["dataset_kind"] == "synthetic_demo":
        summary["warnings"].append("DU LIEU GIA LAP DE KIEM THU; KHONG DUNG METRICS LAM KET QUA DO AN.")
    return summary


def ensure_empty_output(folder: Path) -> None:
    if folder.exists() and any(folder.iterdir()):
        raise DataError(f"Thu muc dau ra da co noi dung: {folder}. Chon thu muc moi de giu ket qua cu.")
    folder.mkdir(parents=True, exist_ok=True)


def assign_splits(cvs: dict[str, dict], seed: int) -> dict[str, str]:
    groups = sorted({text_hash(cv["cv_text"]) for cv in cvs.values()})
    if len(groups) < 3:
        raise DataError("Can it nhat 3 nhom noi dung CV de chia train/validation/test")
    random.Random(seed).shuffle(groups)
    n_test = max(1, round(len(groups) * 0.15))
    n_val = max(1, round(len(groups) * 0.15))
    group_splits = {h: "test" if i < n_test else "validation" if i < n_test + n_val else "train"
                    for i, h in enumerate(groups)}
    return {key: group_splits[text_hash(row["cv_text"])] for key, row in cvs.items()}


def import_wide(source: Path, output: Path, *, label_column: str = "human_label",
                label_source: str = "human", seed: int = 42) -> dict:
    if label_source not in {"human", "heuristic"}:
        raise DataError("label_source phai la human hoac heuristic")
    if label_column == "heuristic_label" and label_source != "heuristic":
        raise DataError("Cot heuristic_label phai giu label_source=heuristic")
    rows = read_csv(source, ("cv_id", "cv_text", "cv_skills_extracted", "jd_id", "jd_description",
                             "jd_required_skills", label_column))
    cvs, jobs, pairs = {}, {}, []
    for row in rows:
        cv = {"cv_id": row["cv_id"].strip(), "cv_text": row["cv_text"].strip(),
              "cv_skills": "; ".join(normalize_skills(row["cv_skills_extracted"])),
              "source": row.get("cv_source_provenance", "").strip()}
        jd = {"jd_id": row["jd_id"].strip(), "jd_title": row.get("jd_title", "").strip(),
              "jd_text": row["jd_description"].strip(),
              "jd_skills": "; ".join(normalize_skills(row["jd_required_skills"])),
              "source": row.get("jd_source_url", "").strip()}
        for record, key, store in ((cv, cv["cv_id"], cvs), (jd, jd["jd_id"], jobs)):
            if key in store and store[key] != record:
                raise DataError(f"Noi dung mau thuan cho id {key}; khong tu dong lay dong dau")
            store[key] = record
        label = parse_label(row[label_column])
        pairs.append({"cv_id": cv["cv_id"], "jd_id": jd["jd_id"],
                      "label": "" if label is None else LABELS[label],
                      "label_source": label_source if label is not None else "",
                      "split": row.get("data_split", "").strip().casefold()})
    if not any(p["split"] for p in pairs):
        splits = assign_splits(cvs, seed)
        for pair in pairs:
            pair["split"] = splits[pair["cv_id"]]
    elif any(not p["split"] for p in pairs):
        raise DataError("Cot data_split chi duoc de trong toan bo hoac dien day du")
    manifest = {"dataset_kind": "imported", "source_filename": source.name, "label_column": label_column,
                "label_source": label_source, "split_seed": seed,
                "provenance_note": "Imported metadata is not independent verification of sources or labels."}
    # Validate in memory before creating output files.
    dataset = Dataset(
        {k: Document(k, r["cv_text"], normalize_skills(r["cv_skills"]), source=r["source"]) for k, r in cvs.items()},
        {k: Document(k, r["jd_text"], normalize_skills(r["jd_skills"]), r["jd_title"], r["source"]) for k, r in jobs.items()},
        [Pair(p["cv_id"], p["jd_id"], parse_label(p["label"]), p["label_source"], p["split"]) for p in pairs], manifest)
    summary = validate(dataset)
    ensure_empty_output(output)
    write_csv(output / "cvs.csv", list(next(iter(cvs.values()))), list(cvs.values()))
    write_csv(output / "jobs.csv", list(next(iter(jobs.values()))), list(jobs.values()))
    write_csv(output / "pairs.csv", list(pairs[0]), pairs)
    write_json(output / "manifest.json", manifest)
    write_json(output / "validation.json", summary)
    return summary


def extract_known_skills(text: str, vocabulary: list[str]) -> tuple[str, ...]:
    """Conservative dictionary extraction; skills can also be supplied explicitly."""
    text = text.casefold()
    found = set()
    for skill in vocabulary:
        aliases = [skill, *(alias for alias, canonical in SKILL_ALIASES.items() if canonical == skill)]
        if any(re.search(r"(?<![\w#+])" + re.escape(term) + r"(?![\w#+])", text) for term in aliases):
            found.add(skill)
    return tuple(sorted(found))
