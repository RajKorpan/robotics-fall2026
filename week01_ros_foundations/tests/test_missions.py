from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from missions import mission_1 as m1
from missions import mission_2 as m2
from missions import mission_3 as m3


def passing_graph():
    endpoints = {
        "/scan": (["/sensor"], ["/behavior", "/rviz2"]),
        "/odom": (["/controller"], ["/evidence"]),
        "/student_cmd_vel": ([], ["/guard", "/evidence"]),
        "/cmd_vel": (["/guard"], ["/controller"]),
    }
    return {
        "captured_at": "2026-08-31T00:00:00Z",
        "nodes": [
            {"name": "/course_cmd_vel_guard"},
            {"name": "/course_evidence_collector"},
            {"name": "/ros_gz_bridge"},
            {"name": "/rviz2"},
        ],
        "topics": [
            {"name": name, "types": [kind], "publishers": endpoints[name][0], "subscribers": endpoints[name][1]}
            for name, kind in m1.REQUIRED_TOPICS.items()
        ],
    }


def passing_mission_one_responses():
    return {
        "mission_1.guided_checks": {key: True for key in m1.GUIDED_CHECKS},
        "mission_1.scan_observation": "I found the ranges field containing LiDAR distance measurements.",
        **{
            f"mission_1.{key}": "This explanation uses multiple live nodes, topics, message types, and endpoint observations as evidence."
            for key in m1.SYNTHESIS_KEYS
        },
    }


class MissionValidationTests(unittest.TestCase):
    def test_mission_three_ignores_commented_starter_marker(self) -> None:
        source = (
            "def front_distance():\n"
            "    return 1.0\n"
            "    # raise NotImplementedError('starter')\n\n"
            "def decide_velocity():\n"
            "    return 0.0\n"
        )
        self.assertTrue(m3._functions_are_implemented(source))

    def test_mission_three_rejects_executable_starter_marker(self) -> None:
        source = (
            "def front_distance():\n"
            "    raise NotImplementedError('starter')\n\n"
            "def decide_velocity():\n"
            "    return 0.0\n"
        )
        self.assertFalse(m3._functions_are_implemented(source))

    def test_mission_one_passes_complete_evidence(self) -> None:
        responses = passing_mission_one_responses()
        self.assertTrue(m1.evaluate(passing_graph(), responses).passed)

    def test_mission_one_rejects_incomplete_guided_tour(self) -> None:
        responses = passing_mission_one_responses()
        responses["mission_1.guided_checks"]["scan_message"] = False
        self.assertFalse(m1.evaluate(passing_graph(), responses).passed)

    def test_mission_one_rejects_short_scaffolded_explanation(self) -> None:
        responses = passing_mission_one_responses()
        responses["mission_1.graph_explanation"] = "Too short"
        self.assertFalse(m1.evaluate(passing_graph(), responses).passed)

    def test_stable_graph_ignores_timestamp_and_samples(self) -> None:
        first = passing_graph()
        second = passing_graph()
        second["captured_at"] = "2026-08-31T00:00:02Z"
        first["samples"] = {"/scan": {"minimum_finite_range": 1.0}}
        second["samples"] = {"/scan": {"minimum_finite_range": 0.5}}
        self.assertEqual(m1.stable_graph(first), m1.stable_graph(second))

    def test_mission_two_requires_all_trials_after_predictions(self) -> None:
        settings = {
            "straight": (0.15, 0.0, 3.0),
            "rotation": (0.0, 0.5, 3.0),
            "curve": (0.15, -0.4, 4.0),
            "curve_modified": (0.12, 0.6, 4.0),
        }
        trials = [
            {
                "trial_type": kind,
                "captured_at": "2026-08-31T00:01:00Z",
                "completed": True,
                "stop_sent": True,
                "linear_x": values[0],
                "angular_z": values[1],
                "duration": values[2],
                "command_started_at": "2026-08-31T00:00:57Z",
                "zero_command_sent_at": "2026-08-31T00:01:00Z",
                "actual_command_duration": 3.0,
                "duration_error": 0.0,
                "observed_path_length": 0.02 if kind == "rotation" else 0.4,
                "displacement": 0.01 if kind == "rotation" else 0.3,
                "heading_change": 1.0 if kind in ("rotation", "curve", "curve_modified") else 0.01,
            }
            for kind, values in settings.items()
        ]
        responses = {
            "mission_2.predictions": {kind: "A complete prediction entered before running the trial." for kind in m2.TRIAL_TYPES},
            "mission_2.prediction_locks": {kind: "2026-08-31T00:00:00Z" for kind in m2.TRIAL_TYPES},
            "mission_2.modified_settings": {"linear_x": 0.12, "angular_z": 0.6, "duration": 4.0},
            **{f"mission_2.{key}": "A sufficiently detailed explanation using evidence from the measurements." for key in m2.SYNTHESIS_KEYS},
        }
        self.assertTrue(m2.evaluate(trials, responses).passed)
        trials[-1]["captured_at"] = "2026-08-30T23:59:00Z"
        self.assertFalse(m2.evaluate(trials, responses).passed)

        trials[-1]["captured_at"] = "2026-08-31T00:01:00Z"
        trials[0]["observed_path_length"] = 0.0
        trials[0]["displacement"] = 0.0
        self.assertFalse(m2.evaluate(trials, responses).passed)

    def test_mission_two_requires_recorded_modified_slider_values(self) -> None:
        settings = {"linear_x": 0.12, "angular_z": 0.6, "duration": 4.0}
        trials = [
            {
                "trial_type": kind,
                "captured_at": "2026-08-31T00:01:00Z",
                "completed": True,
                "stop_sent": True,
                "linear_x": settings["linear_x"] if kind == "curve_modified" else 0.1,
                "angular_z": settings["angular_z"] if kind == "curve_modified" else 0.2,
                "duration": settings["duration"] if kind == "curve_modified" else 3.0,
                "zero_command_sent_at": "2026-08-31T00:01:00Z",
                "actual_command_duration": 3.0,
                "duration_error": 0.0,
                "observed_path_length": 0.02 if kind == "rotation" else 0.4,
                "displacement": 0.01 if kind == "rotation" else 0.3,
                "heading_change": 1.0 if kind in ("rotation", "curve", "curve_modified") else 0.01,
            }
            for kind in m2.TRIAL_TYPES
        ]
        responses = {
            "mission_2.predictions": {kind: "A complete prediction entered before running the trial." for kind in m2.TRIAL_TYPES},
            "mission_2.prediction_locks": {kind: "2026-08-31T00:00:00Z" for kind in m2.TRIAL_TYPES},
            "mission_2.modified_settings": settings,
            **{f"mission_2.{key}": "A sufficiently detailed explanation using evidence from the measurements." for key in m2.SYNTHESIS_KEYS},
        }
        self.assertTrue(m2.evaluate(trials, responses).passed)
        responses["mission_2.modified_settings"] = {"linear_x": 0.2, "angular_z": 0.6, "duration": 4.0}
        self.assertFalse(m2.evaluate(trials, responses).passed)

    def test_mission_three_requires_all_safety_scenarios(self) -> None:
        behavior = {
            "unit_tests_passed": True,
            "command_bounded": True,
            "ros_node_verified": True,
            "scenarios": {name: {"passed": True} for name in m3.SCENARIOS},
        }
        responses = {
            **{f"mission_3.{key}": "A complete explanation of the implemented robot system." for key in m3.EXPLANATION_KEYS},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("week01_behavior/decision.py", "week01_behavior/obstacle_guard.py"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("def front_distance(): pass\ndef decide_velocity(): pass\n" + "x = 1\n" * 30, encoding="utf-8")
            student_test = root / "test/test_student_decision.py"
            student_test.parent.mkdir(parents=True, exist_ok=True)
            student_test.write_text(
                "from week01_behavior.decision import decide_velocity\n"
                "def test_student_decision():\n    assert decide_velocity(0.5, 0.5, 0.08) == 0.0\n"
                + "# student test explanation\n" * 3,
                encoding="utf-8",
            )
            self.assertTrue(m3.evaluate(behavior, passing_graph(), responses, root).passed)
            behavior["scenarios"]["stale_scan"]["passed"] = False
            self.assertFalse(m3.evaluate(behavior, passing_graph(), responses, root).passed)


if __name__ == "__main__":
    unittest.main()
