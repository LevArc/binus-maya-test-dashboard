"""Local run coordination and bounded, token-free metadata storage."""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

MAYA_ORIGIN = "https://binusmaya.binus.ac.id"
DEFAULT_COURSE = "/lms/course/414c7563-6e80-4753-b443-8cd991d7ac3e/session/a731cedf-34b4-432f-9772-6adbec4d4687"


@dataclass
class Config:
    course_path: str = field(default_factory=lambda: os.getenv("MAYA_COURSE_PATH", DEFAULT_COURSE))
    course_title: str = field(default_factory=lambda: os.getenv("MAYA_COURSE_TITLE", "Automation Testing"))
    section: str = field(default_factory=lambda: os.getenv("MAYA_SECTION", "LA83 - LEC"))
    session: str = field(default_factory=lambda: os.getenv("MAYA_SESSION", "Session 2"))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("MAYA_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data"))))


    def __post_init__(self):
        self.data_dir = Path(self.data_dir).resolve()
        parsed = urlsplit(self.course_path)
        if parsed.query or parsed.fragment or parsed.netloc or parsed.scheme or not self.course_path.startswith("/lms/course/"):
            raise ValueError("Course path must be an /lms/course/... path without host, query, or fragment")


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunManager:
    def __init__(self, config=None, runner=None):
        self.config = config or Config()
        if runner is None:
            from .runner import run_maya
            runner = run_maya
        self.runner = runner
        self.root = self.config.data_dir / "runs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.runs = {}
        for path in self.root.glob("*/result.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record["status"] in ("running", "login_required"):
                    record["status"] = "interrupted"
                self.runs[record["id"]] = record
            except (ValueError, KeyError, OSError):
                continue
        self.active = None
        self.version = 0
        self.threads = {}

    def _save(self, record):
        folder = self.root / record["id"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "result.json"
        temp = folder / "result.tmp"
        temp.write_text(json.dumps(record, indent=2), encoding="utf-8")
        temp.replace(path)
        self.version += 1
        self.condition.notify_all()

    def start(self):
        with self.lock:
            if self.active:
                raise RuntimeError("A run is already active")
            run_id = uuid.uuid4().hex
            record = {"id": run_id, "status": "running", "started": timestamp(), "finished": None, "steps": []}
            self.runs[run_id] = record
            self.active = run_id
            self._save(record)
            thread = threading.Thread(target=self._work, args=(run_id,), daemon=True)
            self.threads[run_id] = thread
            thread.start()
            return run_id

    def _work(self, run_id):
        def emit(name, status, detail, count=None, screenshot=None, excerpt=None, duration_ms=None):
            with self.lock:
                record = self.runs[run_id]
                if name == "authentication":
                    record["status"] = "login_required" if status == "waiting" else "running"
                record["steps"].append({"name": name, "status": status, "detail": detail,
                                        "count": count, "screenshot": screenshot, "excerpt": excerpt,
                                        "duration_ms": duration_ms, "at": timestamp()})
                self._save(record)
        try:
            self.runner(self.config, emit, self.root / run_id)
            with self.lock:
                steps = self.runs[run_id]["steps"]
                self.runs[run_id]["status"] = "passed" if all(
                    any(s["name"] == name and s["status"] == "passed" for s in steps)
                    for name in ("schedule", "materials")) else "failed"
        except Exception as exc:
            with self.lock:
                self.runs[run_id]["steps"].append({"name": "run", "status": "failed", "detail": f"Browser or runner failed ({type(exc).__name__}); check the saved profile and navigation.", "count": None, "screenshot": None, "excerpt": None, "at": timestamp()})
                self.runs[run_id]["status"] = "failed"
        finally:
            with self.lock:
                self.runs[run_id]["finished"] = timestamp()
                self.active = None
                self._save(self.runs[run_id])

    def wait(self, run_id, timeout=None):
        self.threads[run_id].join(timeout)

    def get(self, run_id):
        with self.lock:
            record = self.runs.get(run_id)
            return json.loads(json.dumps(record)) if record else None

    def list_runs(self):
        with self.lock:
            return sorted((json.loads(json.dumps(r)) for r in self.runs.values()),
                          key=lambda r: r["started"], reverse=True)

    def changes(self, version, timeout=20):
        with self.condition:
            self.condition.wait_for(lambda: self.version != version, timeout)
            return self.version, self.list_runs()
