import http.client
import json
import threading

import pytest

from cvjd_gnn.demo import make_demo
from cvjd_gnn.predict import predict
from cvjd_gnn.training import TrainConfig, train
from cvjd_gnn.web import InferenceService, make_server


@pytest.fixture(scope="module")
def web_server(tmp_path_factory):
    root = tmp_path_factory.mktemp("web")
    data, runs = root / "data", root / "runs"
    make_demo(data, cvs=18)
    train(data, runs / "test_model", TrainConfig(epochs=2, hidden_channels=8, max_features=64, torch_threads=1))
    server = make_server(runs, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, root
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def request(server, method, path, payload=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=15)
    body = json.dumps(payload).encode() if payload is not None else None
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    status, content, response_headers = response.status, response.read(), dict(response.getheaders())
    connection.close()
    return status, content, response_headers


def test_static_assets_and_catalog_are_available(web_server):
    server, _ = web_server
    for path in ("/", "/assets/app.css", "/assets/app.js", "/favicon.svg"):
        status, content, headers = request(server, "GET", path)
        assert status == 200 and content
        assert headers["X-Content-Type-Options"] == "nosniff"
    status, content, _ = request(server, "GET", "/api/models")
    assert status == 200
    assert json.loads(content)["models"][0]["id"] == "test_model"
    assert request(server, "GET", "/api/health")[0] == 200


def test_web_prediction_is_the_same_as_cli_and_does_not_save_cv(web_server):
    server, root = web_server
    sample = json.loads((root / "data" / "sample_cv.json").read_text())
    before = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    status, content, _ = request(server, "POST", "/api/predict", {**sample, "run_id": "test_model", "top_k": 2})
    assert status == 200
    result = json.loads(content)
    direct = predict(root / "runs" / "test_model", cv_json=root / "data" / "sample_cv.json", top_k=2)
    assert result["ranked_jobs"] == direct["ranked_jobs"]
    assert result["dataset_kind"] == "synthetic_demo"
    after = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    assert after == before


def test_invalid_input_and_foreign_origins_are_rejected(web_server):
    server, _ = web_server
    valid = {"run_id": "test_model", "cv_text": "Python project"}
    assert request(server, "POST", "/api/predict", {**valid, "cv_text": " "})[0] == 400
    assert request(server, "POST", "/api/predict", {**valid, "top_k": 51})[0] == 400
    assert request(server, "POST", "/api/predict", {**valid, "cv_skills": [123]})[0] == 400
    assert request(server, "POST", "/api/predict", valid, {"Origin": "https://example.org"})[0] == 403
    assert request(server, "POST", "/api/predict", valid, {"Content-Type": "text/plain"})[0] == 415
    assert request(server, "POST", "/api/predict", valid, {"Content-Length": "1048577"})[0] == 413


def test_no_arbitrary_file_or_checkpoint_access(web_server):
    server, _ = web_server
    assert request(server, "GET", "/../pyproject.toml")[0] == 404
    assert request(server, "GET", "/runs/test_model/model.pt")[0] == 404
    assert request(server, "GET", "/", headers={"Host": "example.org"})[0] == 403
    status, _, _ = request(server, "POST", "/api/predict", {"run_id": "../test_model", "cv_text": "Python"})
    assert status == 400


def test_missing_run_directory_is_an_empty_catalog(tmp_path):
    assert InferenceService(tmp_path / "not_created").models() == []
