import json

import pytest

from cvjd_gnn.data import DataError
from cvjd_gnn.demo import make_demo
from cvjd_gnn.predict import evaluate, predict
from cvjd_gnn.training import TrainConfig, train


def test_training_checkpoint_reload_and_prediction(tmp_path):
    data, run = tmp_path / "demo", tmp_path / "run"
    make_demo(data, cvs=18)
    config = TrainConfig(epochs=2, patience=2, hidden_channels=8, max_features=64, torch_threads=1)
    metrics = train(data, run, config)
    repeated = evaluate(run, data)
    assert repeated["test"]["macro_f1"] == metrics["gnn"]["test"]["macro_f1"]
    assert repeated["test"]["loss"] == pytest.approx(metrics["gnn"]["test"]["loss"], abs=1e-6)
    assert metrics["dataset_kind"] == "synthetic_demo"
    assert set(metrics["baselines"]["test"]) == {"majority", "skill_overlap_rule", "tfidf_cosine_logistic_regression"}
    report = predict(run, cv_json=data / "sample_cv.json", top_k=2, output=tmp_path / "predictions.csv")
    assert len(report["ranked_jobs"]) == 2
    for row in report["ranked_jobs"]:
        assert 0 <= row["ranking_score"] <= 100
        assert sum(row[key] for key in ("p_low", "p_medium", "p_high")) == pytest.approx(1, abs=1e-6)
    assert json.loads((run / "run.json").read_text())["dataset"]["dataset_kind"] == "synthetic_demo"
    with (data / "cvs.csv").open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(DataError, match="Dataset da thay doi"):
        evaluate(run, data)
