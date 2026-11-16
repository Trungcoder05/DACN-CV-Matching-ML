"""Audit a CV/JD CSV without dependencies or exporting resume text.

Usage: python scripts/audit_dataset.py INPUT.csv --output reports/dataset_audit.json
This reads the source file without modifying it. Labels and provenance in the
CSV are treated as claims to inspect, not as verified recruitment outcomes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skills(text: str) -> set[str]:
    return {part.strip().casefold() for part in text.split(";") if part.strip()}


def distribution(rows: list[dict], field: str) -> dict:
    return dict(Counter(row.get(field, "").strip() for row in rows).most_common())


def lengths(values: list[str]) -> dict:
    sizes = [len(value) for value in values]
    return {"min": min(sizes), "median": statistics.median(sizes), "max": max(sizes)} if sizes else {}


def audit(source: Path) -> dict:
    csv.field_size_limit(50_000_000)
    with source.open("rb") as handle:
        file_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)
    if not rows:
        raise ValueError("CSV has no data rows")
    required = {"cv_id", "jd_id", "cv_text", "jd_description", "data_split", "heuristic_label"}
    if missing := required.difference(columns):
        raise ValueError(f"Missing columns: {sorted(missing)}")
    malformed = [i + 2 for i, row in enumerate(rows) if None in row or any(v is None for v in row.values())]
    if malformed:
        raise ValueError(f"Malformed CSV records (record numbers, not physical lines): {malformed[:10]}")

    cvs, jds = {}, {}
    cv_versions, jd_versions = defaultdict(set), defaultdict(set)
    cv_splits, jd_splits = defaultdict(set), defaultdict(set)
    exact_text_ids, normalized_text_ids = defaultdict(set), defaultdict(set)
    exact_text_splits, normalized_text_splits = defaultdict(set), defaultdict(set)
    normalized_core_splits = defaultdict(set)
    declared_hash_ids = defaultdict(set)
    pairs, pair_ids, pairs_per_cv = Counter(), Counter(), Counter()
    labels_by_split = defaultdict(Counter)
    sampling_by_label = defaultdict(Counter)
    scores_by_label = defaultdict(list)
    overlap_mismatch_count = 0
    invalid_scores = 0
    matched_not_required = 0
    matched_not_in_extracted = 0
    matched_missing_skill_counts = Counter()
    rule_label_mismatches = 0
    declared_hash_mismatch = 0
    scored_rows = 0

    for row in rows:
        cv_id, jd_id, split = row["cv_id"], row["jd_id"], row["data_split"]
        if cv_id not in cvs:
            cvs[cv_id] = row
        if jd_id not in jds:
            jds[jd_id] = row
        text_hash = digest(row["cv_text"])
        normalized_hash = digest(" ".join(row["cv_text"].casefold().split()))
        word_hash = digest(" ".join("".join(c if c.isalnum() else " " for c in row["cv_text"].casefold()).split()))
        cv_versions[cv_id].add(text_hash)
        jd_versions[jd_id].add(tuple(row.get(k, "") for k in ("jd_title", "jd_description", "jd_required_skills", "jd_source_url")))
        cv_splits[cv_id].add(split)
        jd_splits[jd_id].add(split)
        exact_text_ids[text_hash].add(cv_id)
        normalized_text_ids[normalized_hash].add(cv_id)
        exact_text_splits[text_hash].add(split)
        normalized_text_splits[normalized_hash].add(split)
        normalized_core_splits[word_hash].add(split)
        declared_hash = row.get("cv_text_hash", "")
        declared_hash_ids[declared_hash].add(cv_id)
        declared_hash_mismatch += bool(declared_hash) and declared_hash != text_hash
        pairs[(cv_id, jd_id)] += 1
        pair_ids[row.get("pair_id", "")] += 1
        pairs_per_cv[cv_id] += 1
        labels_by_split[split][row["heuristic_label"]] += 1
        sampling_by_label[row.get("pair_sampling_method", "")][row["heuristic_label"]] += 1
        required_skills = skills(row.get("jd_required_skills", ""))
        matched = skills(row.get("matched_skills", ""))
        extracted = skills(row.get("cv_skills_extracted", ""))
        matched_not_required += bool(matched - required_skills)
        matched_not_in_extracted += bool(matched - extracted)
        matched_missing_skill_counts.update(matched - extracted)
        try:
            score = float(row.get("skill_overlap_percent", ""))
            if not math.isfinite(score) or not 0 <= score <= 100:
                raise ValueError("Score outside [0, 100]")
            scores_by_label[row["heuristic_label"]].append(score)
            reconstructed_label = "Thấp" if score < 40 else "Trung bình" if score < 60 else "Cao"
            rule_label_mismatches += row["heuristic_label"] != reconstructed_label
            if required_skills:
                scored_rows += 1
                expected = len(matched & required_skills) / len(required_skills) * 100
                overlap_mismatch_count += abs(score - expected) > 0.500001
        except ValueError:
            invalid_scores += 1

    cv_rows, jd_rows = list(cvs.values()), list(jds.values())
    cv_skill_edges = {(key, skill) for key, row in cvs.items() for skill in skills(row.get("cv_skills_extracted", ""))}
    jd_skill_edges = {(key, skill) for key, row in jds.items() for skill in skills(row.get("jd_required_skills", ""))}
    all_skills = {skill for _, skill in cv_skill_edges | jd_skill_edges}
    label_counts = Counter(row["heuristic_label"] for row in rows)
    cv_metadata_fields = ["cv_category", "cv_real_person_verified", "cv_source_provenance", "seniority_signal", "internship_scope", "cv_template_indicator", "cv_has_template_signal", "cv_is_intern_verified", "cv_privacy_audit", "education_evidence", "experience_evidence", "project_evidence"]
    pair_metadata_fields = ["label_provenance", "label_is_expert_verified", "cv_jd_label_type", "pair_sampling_method", "quality_flags", "cv_split_leakage_control", "suitable_for_expert_evaluation"]
    jd_metadata_fields = ["jd_company", "jd_family", "jd_source_type", "jd_is_real_posting", "jd_posting_active_verified", "jd_is_internship_intended", "jd_source_verification_level"]
    split_stats = {}
    for split in sorted(labels_by_split):
        subset = [row for row in rows if row["data_split"] == split]
        counts = labels_by_split[split]
        split_stats[split] = {
            "pairs": len(subset), "unique_cvs": len({r["cv_id"] for r in subset}),
            "unique_jds": len({r["jd_id"] for r in subset}), "labels": dict(counts),
            "majority_accuracy_percent": round(max(counts.values()) / len(subset) * 100, 4),
        }

    return {
        "source": {"path": str(source), "bytes": source.stat().st_size, "sha256": file_hash},
        "rows": len(rows), "column_count": len(columns), "columns": columns,
        "unique_cv_ids": len(cvs), "unique_jd_ids": len(jds),
        "unique_exact_cv_texts": len(exact_text_ids), "unique_normalized_cv_texts": len(normalized_text_ids),
        "unique_jd_description_texts": len({r["jd_description"] for r in jd_rows}),
        "unique_jd_urls": len({r.get("jd_source_url", "") for r in jd_rows}),
        "empty_values_by_column": {key: sum(not row[key].strip() for row in rows) for key in columns},
        "duplicate_pair_rows": sum(n - 1 for n in pairs.values()),
        "duplicate_pair_id_rows": sum(n - 1 for n in pair_ids.values()),
        "pairs_per_cv_distribution": dict(Counter(pairs_per_cv.values())),
        "cv_ids_with_inconsistent_text": sum(len(v) > 1 for v in cv_versions.values()),
        "jd_ids_with_inconsistent_content": sum(len(v) > 1 for v in jd_versions.values()),
        "exact_cv_text_groups_with_multiple_ids": sum(len(v) > 1 for v in exact_text_ids.values()),
        "normalized_cv_text_groups_with_multiple_ids": sum(len(v) > 1 for v in normalized_text_ids.values()),
        "declared_hash_mismatch_rows_against_raw_utf8_sha256": declared_hash_mismatch,
        "declared_hash_note": "Stored hashes may use an undocumented text normalization. Mismatches do not by themselves prove corruption; split checks above use independently computed hashes of the actual text.",
        "splits": split_stats,
        "split_overlap": {
            "cv_ids_in_multiple_splits": sum(len(v) > 1 for v in cv_splits.values()),
            "exact_cv_texts_in_multiple_splits": sum(len(v) > 1 for v in exact_text_splits.values()),
            "normalized_cv_texts_in_multiple_splits": sum(len(v) > 1 for v in normalized_text_splits.values()),
            "alphanumeric_normalized_cv_texts_in_multiple_splits": sum(len(v) > 1 for v in normalized_core_splits.values()),
            "jd_ids_in_multiple_splits": sum(len(v) > 1 for v in jd_splits.values()),
            "note": "Exact and normalized comparisons do not establish absence of near duplicates or shared identities. Shared JD IDs are consistent with an unseen-CV/known-JD evaluation, not unseen-JD generalization.",
        },
        "labels": dict(label_counts),
        "majority_accuracy_percent": round(max(label_counts.values()) / len(rows) * 100, 4),
        "human_labels_nonempty": sum(bool(row.get("human_label", "").strip()) for row in rows),
        "score_ranges_by_label": {label: {"min": min(values), "max": max(values), "distinct": sorted(set(values))} for label, values in scores_by_label.items()},
        "score_reconstruction": {
            "method": "100 * |provided matched_skills intersect required_skills| / |required_skills|, casefolded semicolon lists; tolerance 0.500001 percentage points for integer rounding",
            "rows_checked": scored_rows, "mismatch_rows": overlap_mismatch_count,
            "invalid_score_rows": invalid_scores, "rows_with_matched_skills_outside_required": matched_not_required,
            "rows_with_matched_skills_absent_from_extracted_cv_skills": matched_not_in_extracted,
            "matched_skills_absent_from_cv_extraction_frequency": dict(matched_missing_skill_counts.most_common()),
            "label_rule_checked": "score < 40: Thấp; 40 <= score < 60: Trung bình; score >= 60: Cao",
            "label_rule_mismatch_rows": rule_label_mismatches,
        },
        "cv_metadata_distributions_unique_cv": {key: distribution(cv_rows, key) for key in cv_metadata_fields},
        "jd_metadata_distributions_unique_jd": {key: distribution(jd_rows, key) for key in jd_metadata_fields},
        "pair_metadata_distributions": {key: distribution(rows, key) for key in pair_metadata_fields},
        "sampling_method_by_label": {key: dict(value) for key, value in sampling_by_label.items()},
        "cv_text_character_lengths": lengths([r["cv_text"] for r in cv_rows]),
        "jd_description_character_lengths": lengths([r["jd_description"] for r in jd_rows]),
        "candidate_graph_counts": {
            "cv_nodes": len(cvs), "jd_nodes": len(jds), "skill_nodes_casefold_only": len(all_skills),
            "cv_skill_edges": len(cv_skill_edges), "jd_skill_edges": len(jd_skill_edges),
            "cvs_without_extracted_skills": sum(not skills(r.get("cv_skills_extracted", "")) for r in cv_rows),
            "note": "Structural counts only; no graph model was trained, no skill aliases were reconciled, and CV-JD labels must not be blindly added as training edges.",
        },
        "jds": [{key: row.get(key, "") for key in ("jd_id", "jd_company", "jd_title", "jd_family", "jd_description", "jd_required_skills", "jd_source_url")} for row in sorted(jd_rows, key=lambda r: r["jd_id"])],
        "limitations": ["Original CV provenance and human identities are not verified by this script.", "JD source URLs are recorded but not fetched by this script.", "No expert assessment of CV-JD suitability has been performed.", "No semantic near-duplicate detection or full privacy audit has been performed."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_keys = ["rows", "column_count", "unique_cv_ids", "unique_jd_ids", "unique_exact_cv_texts", "unique_normalized_cv_texts", "duplicate_pair_rows", "pairs_per_cv_distribution", "splits", "split_overlap", "labels", "majority_accuracy_percent", "human_labels_nonempty", "score_ranges_by_label", "score_reconstruction", "cv_metadata_distributions_unique_cv", "jd_metadata_distributions_unique_jd", "pair_metadata_distributions", "cv_text_character_lengths", "jd_description_character_lengths", "candidate_graph_counts"]
    print(json.dumps({key: result[key] for key in summary_keys}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
