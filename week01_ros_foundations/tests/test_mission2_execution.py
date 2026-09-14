from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from missions.mission_2 import motion_observed
from pages import mission_2


class MissionTwoExecutionTests(unittest.TestCase):
    @patch("pages.mission_2.os.killpg", create=True)
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

    @patch("pages.mission_2.save_motion_trial")
    @patch("pages.mission_2.os.killpg", create=True)
    @patch("pages.mission_2.motion_trials", return_value=[])
    @patch("pages.mission_2.subprocess.Popen")
    def test_started_timeout_saves_labeled_backup_and_allows_progress(
        self,
        popen: MagicMock,
        motion_trials: MagicMock,
        killpg: MagicMock,
        save_motion_trial: MagicMock,
    ) -> None:
        process = popen.return_value
        process.pid = 1234
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("trial", 48),
            ("[INFO] [timed_twist_trial]: Starting straight for 3.00s", ""),
        ]

        passed, message = mission_2._run_trial("straight", 0.15, 0.0, 3.0)

        self.assertTrue(passed)
        self.assertIn("backup model", message)
        backup = save_motion_trial.call_args.args[0]
        self.assertTrue(backup["completed"])
        self.assertTrue(backup["stop_sent"])
        self.assertTrue(backup["fallback_used"])
        self.assertAlmostEqual(backup["displacement"], 0.4095)
        self.assertLess(backup["observed_path_length"], backup["commanded_path_length"])
        self.assertAlmostEqual(backup["duration_error"], 0.03)
        killpg.assert_called_once()

    def test_backup_models_cover_every_mission_two_motion(self) -> None:
        cases = {
            "straight": (0.15, 0.0, 3.0),
            "rotation": (0.0, 0.5, 3.0),
            "curve": (0.15, -0.4, 4.0),
            "curve_modified": (0.12, 0.6, 4.0),
        }

        for name, (linear_x, angular_z, duration) in cases.items():
            with self.subTest(trial=name):
                backup = mission_2._backup_trial(name, linear_x, angular_z, duration)
                self.assertTrue(backup["completed"])
                self.assertTrue(backup["stop_sent"])
                self.assertTrue(backup["fallback_used"])
                self.assertEqual(backup["evidence_source"], "representative backup model")
                self.assertAlmostEqual(
                    backup["heading_change"],
                    angular_z * duration * mission_2.BACKUP_ANGULAR_RESPONSE,
                )
                self.assertTrue(motion_observed(name, backup))

        rotation = mission_2._backup_trial("rotation", 0.0, 0.5, 3.0)
        self.assertGreater(rotation["displacement"], 0.0)
        self.assertLess(rotation["heading_change"], 0.5 * 3.0)
        self.assertGreater(rotation["heading_change"], 0.0)

        guided_curve = mission_2._backup_trial("curve", 0.15, -0.4, 4.0)
        modified_curve = mission_2._backup_trial("curve_modified", 0.12, 0.6, 4.0)
        self.assertLess(guided_curve["heading_change"], 0.0)
        self.assertGreater(modified_curve["heading_change"], 0.0)
        self.assertLess(guided_curve["observed_path_length"], guided_curve["commanded_path_length"])
        self.assertLess(modified_curve["observed_path_length"], modified_curve["commanded_path_length"])

    @patch("pages.mission_2.save_motion_trial")
    @patch("pages.mission_2.subprocess.Popen")
    def test_gazebo_service_timeout_uses_backup_and_unlocks_progress(
        self,
        popen: MagicMock,
        save_motion_trial: MagicMock,
    ) -> None:
        process = popen.return_value
        process.returncode = 1
        process.communicate.return_value = ("", "Service call timed out")

        passed, message = mission_2._run_trial("curve", 0.15, -0.4, 4.0)

        self.assertTrue(passed)
        self.assertIn("Gazebo did not answer", message)
        backup = save_motion_trial.call_args.args[0]
        self.assertEqual(backup["trial_type"], "curve")
        self.assertTrue(backup["fallback_used"])

    @patch("pages.mission_2.save_motion_trial")
    @patch("pages.mission_2.os.killpg", create=True)
    @patch("pages.mission_2.motion_trials", return_value=[])
    @patch("pages.mission_2.subprocess.Popen")
    def test_timeout_without_process_output_still_unlocks_progress(
        self,
        popen: MagicMock,
        motion_trials: MagicMock,
        killpg: MagicMock,
        save_motion_trial: MagicMock,
    ) -> None:
        process = popen.return_value
        process.pid = 1234
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("trial", 48),
            ("", ""),
        ]

        passed, message = mission_2._run_trial("straight", 0.15, 0.0, 3.0)

        self.assertTrue(passed)
        self.assertIn("backup model", message)
        backup = save_motion_trial.call_args.args[0]
        self.assertEqual(backup["trial_type"], "straight")
        self.assertTrue(backup["fallback_used"])
        killpg.assert_called_once()

    def test_preflight_uses_colored_status_labels(self) -> None:
        source = (mission_2.ROOT / "pages" / "preflight.py").read_text(encoding="utf-8")
        self.assertIn(":green[✔ Passed]", source)
        self.assertIn(":red[✘ Not ready]", source)

    @patch("pages.mission_2.subprocess.run")
    def test_reset_uses_nonblocking_pose_backup_after_pose_timeout(self, run: MagicMock) -> None:
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "published", ""),
            subprocess.TimeoutExpired("pose reset", 12),
            subprocess.CompletedProcess([], 0, "data: true", ""),
        ]

        confirmed, message = mission_2._reset_robot()

        self.assertTrue(confirmed)
        self.assertIn("backup reset", message)
        self.assertIn("/world/default/set_pose", run.call_args_list[2].args[0][2])
        self.assertNotIn("set_pose/blocking", run.call_args_list[2].args[0][2])

    @patch("pages.mission_2.subprocess.run")
    def test_unconfirmed_reset_does_not_prevent_mission_completion(self, run: MagicMock) -> None:
        run.side_effect = [
            subprocess.TimeoutExpired("stop", 8),
            subprocess.TimeoutExpired("pose reset", 12),
            subprocess.TimeoutExpired("world reset", 12),
        ]

        confirmed, message = mission_2._reset_robot()

        self.assertFalse(confirmed)
        self.assertIn("Mission 2 was saved", message)
        self.assertIn("continue to Mission 3", message)

    def test_mission_two_resets_before_mission_three(self) -> None:
        source = (mission_2.ROOT / "pages" / "mission_2.py").read_text(encoding="utf-8")
        self.assertIn("def _reset_robot", source)
        self.assertIn("reset_confirmed, reset_message = _reset_robot()", source)
        self.assertIn('"reset_confirmed": reset_confirmed', source)
        self.assertIn("Continue to Mission 3", source)
        self.assertIn('set_stage(st, "mission_3")', source)


if __name__ == "__main__":
    unittest.main()
