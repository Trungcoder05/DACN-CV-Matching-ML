"""Local-only web interface. Serves a fixed asset list and in-memory inference."""

from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .data import DataError

ASSETS = Path(__file__).parent / "web_assets"
RUN_FILES = ("run.json", "model.pt", "text_encoder.json", "graph_metadata.json", "graph_context.pt", "job_catalog.json")
MAX_BODY = 1_048_576
MAX_TEXT = 100_000
SAMPLE = {"cv_text": "SYNTHETIC DEMO CV. Student with a Django project using Python, SQL and Git.",
          "cv_skills": ["Python", "Django", "SQL", "Git"]}


class InferenceService:
    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir.resolve()
        self._lock = threading.Lock()
        self._cache_key = None
        self._loaded = None

    def models(self) -> list[dict]:
        models = []
        if not self.runs_dir.is_dir():
            return models
        for folder in self.runs_dir.iterdir():
            if not folder.is_dir() or not folder.resolve().is_relative_to(self.runs_dir):
                continue
            if not all((folder / filename).is_file() for filename in RUN_FILES):
                continue
            try:
                run = json.loads((folder / "run.json").read_text(encoding="utf-8"))
                dataset = run["dataset"]
                splits = dataset.get("splits", {})
                weak = any(info.get("label_sources", {}).get("heuristic", 0) for info in splits.values())
                models.append({"id": folder.name, "dataset_kind": dataset.get("dataset_kind", "unspecified"),
                               "created_at": run.get("created_at_utc", ""), "cv_count": dataset.get("cvs", 0),
                               "job_count": dataset.get("jobs", 0), "pair_count": dataset.get("pairs", 0),
                               "has_weak_labels": weak})
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                continue
        return sorted(models, key=lambda model: (model["created_at"], model["id"]), reverse=True)

    def analyze(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise DataError("Dữ liệu gửi lên phải là JSON object.")
        run_id, text = payload.get("run_id"), payload.get("cv_text", "")
        if not isinstance(run_id, str) or run_id not in {model["id"] for model in self.models()}:
            raise DataError("Mô hình không tồn tại hoặc chưa có đủ tệp. Hãy chọn lại mô hình.")
        if not isinstance(text, str) or not text.strip():
            raise DataError("Bạn chưa nhập nội dung CV.")
        if len(text) > MAX_TEXT:
            raise DataError("CV quá dài. Vui lòng giới hạn ở 100.000 ký tự.")
        top_k = payload.get("top_k", 5)
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 50:
            raise DataError("Số kết quả phải nằm trong khoảng 1–50.")
        folder = (self.runs_dir / run_id).resolve()
        if not folder.is_relative_to(self.runs_dir):
            raise DataError("Đường dẫn mô hình không hợp lệ.")
        from .predict import load_run, predict_record

        with self._lock:
            signature = (str(folder), tuple((name, (folder / name).stat().st_mtime_ns,
                                             (folder / name).stat().st_size) for name in RUN_FILES))
            if signature != self._cache_key:
                loaded = load_run(folder)
                self._loaded, self._cache_key = loaded, signature
            result = predict_record(folder, {"cv_text": text, "cv_skills": payload.get("cv_skills")},
                                    top_k=top_k, loaded_run=self._loaded)
        return {**result, "run_id": run_id}


def make_server(runs_dir: Path, port: int = 8000) -> ThreadingHTTPServer:
    service = InferenceService(runs_dir)

    class Handler(BaseHTTPRequestHandler):
        server_version = "CVMatch/1.0"
        sys_version = ""

        def setup(self):
            super().setup()
            self.connection.settimeout(30)

        def log_message(self, format, *args):
            # Do not log CVs, filenames, raw query strings or request bodies.
            return

        def local_request(self) -> bool:
            port = self.server.server_port
            allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host", "").casefold() not in allowed:
                self.json_response(403, {"error": "Chỉ phục vụ trên localhost."})
                return False
            origin = self.headers.get("Origin")
            if origin is not None and origin not in {f"http://{host}" for host in allowed}:
                self.json_response(403, {"error": "Nguồn yêu cầu không được phép."})
                return False
            return True

        def respond(self, status: int, content: bytes, content_type: str):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; "
                             "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                             "base-uri 'none'; frame-ancestors 'none'")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            if self.command != "HEAD":
                self.wfile.write(content)

        def json_response(self, status: int, value: dict):
            self.respond(status, json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8"),
                         "application/json; charset=utf-8")

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if not self.local_request():
                return
            path = urlsplit(self.path).path
            if path == "/api/health":
                self.json_response(200, {"status": "ok", "app": "cvjd-gnn"})
            elif path == "/api/models":
                self.json_response(200, {"models": service.models()})
            elif path == "/api/sample":
                self.json_response(200, SAMPLE)
            else:
                assets = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/assets/app.css": ("app.css", "text/css; charset=utf-8"),
                          "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
                          "/favicon.svg": ("favicon.svg", "image/svg+xml")}
                if path not in assets:
                    self.json_response(404, {"error": "Không tìm thấy trang."})
                    return
                filename, mime = assets[path]
                self.respond(200, (ASSETS / filename).read_bytes(), mime)

        def do_POST(self):
            if not self.local_request():
                return
            if urlsplit(self.path).path != "/api/predict":
                self.json_response(404, {"error": "Không tìm thấy chức năng."})
                return
            if self.headers.get_content_type() != "application/json":
                self.json_response(415, {"error": "Yêu cầu cần có định dạng JSON."})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = 0
            if size <= 0 or size > MAX_BODY:
                self.json_response(413, {"error": "Nội dung gửi lên phải có kích thước từ 1 byte đến 1 MB."})
                return
            try:
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
                result = service.analyze(payload)
                self.json_response(200, result)
            except (DataError, ValueError, UnicodeError) as exc:
                self.json_response(400, {"error": str(exc)})
            except OSError:
                self.json_response(503, {"error": "Không đọc được mô hình. Vui lòng tải lại danh sách và thử lại."})
            except Exception:
                logging.exception("Prediction failed")
                self.json_response(500, {"error": "Chưa thể phân tích CV. Kiểm tra mô hình đã lưu và thử lại."})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server


def serve(runs_dir: Path, port: int = 8000):
    if not 1 <= port <= 65535:
        raise DataError("Cổng phải nằm trong khoảng 1–65535.")
    with make_server(runs_dir, port) as server:
        print(f"CVMatch dang chay: http://127.0.0.1:{server.server_port}", flush=True)
        print("Mo dia chi tren trong trinh duyet. Nhan Ctrl+C de dung.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nDa dung may chu web.")
