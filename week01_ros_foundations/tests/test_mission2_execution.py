from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from pages import mission_2


class MissionTwoExecutionTests(unittest.TestCase):
    @patch("pages.mission_2.os.killpg")
    @patch("pages.mission_2.motion_trials")
    @patch("pages.mission_2.subprocess.Popen")
    def test_saved_motion_is_success_if_ros_helper_hangs(
        self,
        popen: MagicMock,
        motion_trials: MagicMock,
        killpg: MagicMock,
    ) -> None:
        process = popen.return_value
        process.pid = 1234
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("trial", 23),
            ("Saved trial", ""),
        ]
        motion_trials.return_value = [
            {
                "trial_type": "straight",
                "captured_at": "9999-01-01T00:00:00+00:00",
                "completed": True,
                "stop_sent": True,
                "observed_path_length": 0.4,
                "displacement": 0.4,
            }
        ]

        passed, message = mission_2._run_trial("straight", 0.15, 0.0, 3.0)

        self.assertTrue(passed)
        self.assertIn("saved the required measurements", message)
        killpg.assert_called_once()

    def test_preflight_uses_colored_status_labels(self) -> None:
        source = (mission_2.ROOT / "pages" / "preflight.py").read_text(encoding="utf-8")
        self.assertIn(":green[✔ Passed]", source)
        self.assertIn(":red[✘ Not ready]", source)

    def test_mission_two_resets_before_mission_three(self) -> None:
        source = (mission_2.ROOT / "pages" / "mission_2.py").read_text(encoding="utf-8")
        self.assertIn("def _reset_robot", source)
        self.assertIn("reset_ok, reset_message = _reset_robot()", source)
        self.assertIn('set_stage(st, "mission_3")', source)


if __name__ == "__main__":
    unittest.main()
