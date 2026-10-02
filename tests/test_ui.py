import json
import shutil
import subprocess
import unittest
from pathlib import Path


class DashboardUiTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required for UI smoke test")
    def test_history_hides_startup_authentication_but_keeps_real_auth_failure(self):
        script = Path(__file__).resolve().parents[1] / "static" / "app.js"
        payload = [
            {"name": "authentication", "status": "running", "detail": "Opening the saved local Chrome profile."},
            {"name": "schedule", "status": "passed"},
        ]
        js = '''const fs=require("fs"), vm=require("vm");
const source=fs.readFileSync(process.argv[1],"utf8").split("byId('start').addEventListener")[0];
const steps=JSON.parse(process.argv[2]);
const result=vm.runInNewContext(source+"\\nlatestSteps({steps})",{steps});
process.stdout.write(JSON.stringify(result));'''
        def visible(steps):
            result = subprocess.run(["node", "-e", js, str(script), json.dumps(steps)],
                                    capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        self.assertEqual([step["name"] for step in visible(payload)], ["schedule"])
        payload.append({"name": "authentication", "status": "failed", "detail": "Session unavailable"})
        self.assertCountEqual([step["name"] for step in visible(payload)], ["authentication", "schedule"])


if __name__ == "__main__":
    unittest.main()
