from dataclasses import replace

import pytest

from cvjd_gnn.data import (DataError, extract_known_skills, import_wide, load_dataset,
                           normalize_skills, save_dataset, validate, write_csv)
from cvjd_gnn.demo import make_demo


@pytest.fixture
def demo(tmp_path):
    folder = tmp_path / "demo"
    make_demo(folder, cvs=18)
    return folder, load_dataset(folder)


def test_detects_duplicate_content_across_splits_even_with_different_ids(demo):
    _, dataset = demo
    train_id, test_id = dataset.cv_ids("train")[0], dataset.cv_ids("test")[0]
    dataset.cvs[test_id] = replace(dataset.cvs[test_id], text="  " + dataset.cvs[train_id].text.upper() + "\n")
    with pytest.raises(DataError, match="noi dung CV trung"):
        validate(dataset)


def test_rejects_conflicting_or_duplicate_pairs(demo):
    _, dataset = demo
    dataset.pairs.append(replace(dataset.pairs[0], label=2))
    with pytest.raises(DataError, match="bi lap"):
        validate(dataset)


def test_weak_labels_require_explicit_training_opt_in(demo):
    _, dataset = demo
    dataset.pairs = [replace(p, label_source="heuristic") for p in dataset.pairs]
    dataset.manifest = {"dataset_kind": "imported"}
    with pytest.raises(DataError, match="allow-weak-labels"):
        validate(dataset, for_training=True)
    assert validate(dataset, for_training=True, allow_weak=True)["pairs"] == 54


def test_import_does_not_replace_missing_human_labels_with_heuristics(demo, tmp_path):
    _, dataset = demo
    rows = []
    for p in dataset.pairs:
        cv, jd = dataset.cvs[p.cv_id], dataset.jobs[p.jd_id]
        rows.append({"cv_id": cv.id, "cv_text": cv.text, "cv_skills_extracted": ";".join(cv.skills),
                     "jd_id": jd.id, "jd_description": jd.text, "jd_required_skills": ";".join(jd.skills),
                     "human_label": "", "heuristic_label": str(p.label), "data_split": p.split})
    source = tmp_path / "wide.csv"
    write_csv(source, list(rows[0]), rows)
    output = tmp_path / "imported"
    import_wide(source, output)
    imported = load_dataset(output)
    assert all(p.label is None for p in imported.pairs)
    with pytest.raises(DataError, match="chua co nhan"):
        validate(imported, for_training=True)
    rows[-1]["cv_text"] = "conflicting content for the same cv id"
    write_csv(source, list(rows[0]), rows)
    with pytest.raises(DataError, match="mau thuan"):
        import_wide(source, tmp_path / "bad")


def test_skill_names_keep_language_boundaries():
    assert normalize_skills("ReactJS; react; C++; c#; NodeJS") == ("c#", "c++", "node.js", "react")
    found = extract_known_skills("JavaScript, C++ and ReactJS project.", ["java", "javascript", "c", "c++", "react"])
    assert found == ("c++", "javascript", "react")


def test_existing_dataset_is_not_overwritten(demo):
    folder, dataset = demo
    before = (folder / "cvs.csv").read_bytes()
    with pytest.raises(DataError, match="da co noi dung"):
        save_dataset(dataset, folder)
    assert (folder / "cvs.csv").read_bytes() == before


def test_prepare_assigns_reproducible_splits_when_all_are_empty(demo, tmp_path):
    folder, _ = demo
    import csv
    with (folder / "pairs.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["split"] = ""
    write_csv(folder / "pairs.csv", list(rows[0]), rows)
    first, second = load_dataset(folder, split_seed=123), load_dataset(folder, split_seed=123)
    assert first.pairs == second.pairs
    assert all(first.cv_ids(split) for split in ("train", "validation", "test"))
    save_dataset(first, tmp_path / "prepared")
    validate(load_dataset(tmp_path / "prepared"), for_training=True)
