from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.models import MissionCheck, RequirementResult
from lab.submissions import save_mission
from missions import MISSIONS


class SubmissionTests(unittest.TestCase):
    def test_mission_submission_contains_standard_artifacts(self) -> None:
        mission = MISSIONS["mission_1"]
        result = mission.run({"gain": 1.0, "target": 1.0, "disturbance": 0.0, "sensor_noise": 0.0})
        check = MissionCheck(True, "passed", [RequirementResult("error", "Error", True, 0.01, "< 0.08")])
        with tempfile.TemporaryDirectory() as directory:
            with patch("lab.submissions.submission_root", return_value=Path(directory)):
                target = save_mission(result, check, {"explain": "Evidence-based answer."})
            expected = {"latest_run.json", "submission.json", "explanation.md", "run.csv"}
            self.assertTrue(expected.issubset({path.name for path in target.iterdir()}))
            payload = json.loads((target / "submission.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], result.run_id)
            self.assertTrue(payload["passed"])


if __name__ == "__main__":
    unittest.main()

