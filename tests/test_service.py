import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from maya_dashboard.service import Config, RunManager


class ServiceTests(unittest.TestCase):
    def test_runner_error_reports_type_without_leaking_message(self):
        with tempfile.TemporaryDirectory() as folder:
            def runner(config, emit, evidence_dir):
                raise RuntimeError("token=top-secret")
            manager = RunManager(Config(data_dir=Path(folder)), runner=runner)
            run_id = manager.start()
            manager.wait(run_id, 3)
            detail = manager.get(run_id)["steps"][-1]["detail"]
            self.assertIn("RuntimeError", detail)
            self.assertNotIn("top-secret", detail)

    def test_config_rejects_external_or_query_based_paths(self):
        for value in ("https://evil.example/x", "//evil.example/x", "/lms/schedule?token=abc", "/logout"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Config(course_path=value)

    def test_manager_rejects_overlapping_runs_and_persists_result(self):
        with tempfile.TemporaryDirectory() as folder:
            started = __import__("threading").Event()
            release = __import__("threading").Event()

            def runner(config, emit, evidence_dir):
                started.set()
                release.wait(3)
                emit("schedule", "passed", "2 class cards", 2)
                emit("materials", "passed", "1 material item", 1)

            manager = RunManager(Config(data_dir=Path(folder)), runner=runner)
            run_id = manager.start()
            self.assertTrue(started.wait(2))
            with self.assertRaisesRegex(RuntimeError, "already active"):
                manager.start()
            release.set()
            manager.wait(run_id, 3)
            run = manager.get(run_id)
            self.assertEqual(run["status"], "passed")
            self.assertEqual(len(run["steps"]), 2)
            reloaded = RunManager(Config(data_dir=Path(folder)), runner=Mock())
            self.assertEqual(reloaded.get(run_id)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
