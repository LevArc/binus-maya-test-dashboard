import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from maya_dashboard.app import create_app
from maya_dashboard.service import Config, RunManager


class ApiTests(unittest.TestCase):
    def test_start_status_history_and_local_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            def runner(config, emit, evidence_dir):
                (evidence_dir / "schedule.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture")
                emit("schedule", "passed", "1 class cards", 1, screenshot="schedule.png")
                emit("materials", "passed", "1 material items", 1)
            manager = RunManager(Config(data_dir=Path(folder)), runner=runner)
            with TestClient(create_app(manager)) as client:
                self.assertEqual(client.get("/").status_code, 200)
                response = client.post("/api/runs")
                self.assertEqual(response.status_code, 202)
                run_id = response.json()["id"]
                manager.wait(run_id, 3)
                self.assertEqual(client.get(f"/api/runs/{run_id}").json()["status"], "passed")
                self.assertEqual(len(client.get("/api/runs").json()), 1)
                self.assertEqual(client.get(f"/api/runs/{run_id}/evidence/schedule.png").status_code, 200)
                self.assertEqual(client.get(f"/api/runs/{run_id}/evidence/../result.json").status_code, 404)
                self.assertEqual(client.get("/api/runs/missing").status_code, 404)
                self.assertEqual(client.post("/api/runs", headers={"host": "evil.example", "origin": "http://evil.example"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
