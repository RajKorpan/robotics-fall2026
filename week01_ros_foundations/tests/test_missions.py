from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from missions import mission_1 as m1
from missions import mission_2 as m2
from missions import mission_3 as m3


def passing_graph():
    return {
        "captured_at": "2026-08-31T00:00:00Z",
        "nodes": [{"name": f"/node_{index}"} for index in range(5)] + [{"name": "/obstacle_guard"}],
        "topics": [{"name": name, "types": [kind]} for name, kind in m1.REQUIRED_TOPICS.items()],
    }


class MissionValidationTests(unittest.TestCase):
    def test_mission_one_passes_complete_evidence(self) -> None:
        responses = {
            "mission_1.node_roles": {f"/node_{index}": "Infrastructure" for index in range(5)},
            "mission_1.topic_types": dict(m1.REQUIRED_TOPICS),
            "mission_1.connections": dict(m1.REQUIRED_CONNECTION_ANSWERS),
            **{f"mission_1.{key}": "Explanation" for key in m1.REFLECTION_KEYS},
        }
        self.assertTrue(m1.evaluate(passing_graph(), responses).passed)

    def test_mission_one_rejects_wrong_command_path(self) -> None:
        responses = {
            "mission_1.node_roles": {f"/node_{index}": "Infrastructure" for index in range(5)},
            "mission_1.topic_types": dict(m1.REQUIRED_TOPICS),
            "mission_1.connections": {**m1.REQUIRED_CONNECTION_ANSWERS, "guard_output": "/scan"},
            **{f"mission_1.{key}": "Explanation" for key in m1.REFLECTION_KEYS},
        }
        self.assertFalse(m1.evaluate(passing_graph(), responses).passed)

    def test_mission_two_requires_modified_curve(self) -> None:
        trials = [
            {"trial_type": kind, "captured_at": "2026-08-31T00:01:00Z", "completed": True, "stop_sent": True, "linear_x": 0.1, "angular_z": 0.2}
            for kind in m2.TRIAL_TYPES
        ]
        responses = {
            "mission_2.predictions": {kind: "Prediction" for kind in (*m2.TRIAL_TYPES, "curve_modified")},
            "mission_2.predictions_locked_at": "2026-08-31T00:00:00Z",
            "mission_2.target_reached": True,
            "mission_2.command_path": "Detailed path " * 10,
            **{f"mission_2.{key}": "Explanation" for key in m2.REFLECTION_KEYS},
        }
        self.assertFalse(m2.evaluate(trials, responses).passed)
        trials.append({"trial_type": "curve_modified", "captured_at": "2026-08-31T00:02:00Z", "completed": True, "stop_sent": True, "linear_x": 0.1, "angular_z": 0.3})
        self.assertTrue(m2.evaluate(trials, responses).passed)

    def test_mission_three_requires_all_safety_scenarios(self) -> None:
        behavior = {
            "unit_tests_passed": True,
            "command_bounded": True,
            "ros_node_verified": True,
            "scenarios": {name: {"passed": True} for name in m3.SCENARIOS},
        }
        responses = {
            "mission_3.design": {key: "safe" for key in ("front_width", "stop_distance", "forward_speed", "invalid_policy", "stale_policy")},
            "mission_3.failure_investigation": "Prediction, failure evidence, restoration, and analysis. " * 3,
            **{f"mission_3.{key}": "Explanation" for key in m3.REFLECTION_KEYS},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("week01_behavior/decision.py", "week01_behavior/obstacle_guard.py", "test/test_decision.py"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# valid source\n" + "x = 1\n" * 30, encoding="utf-8")
            self.assertTrue(m3.evaluate(behavior, passing_graph(), responses, root).passed)
            behavior["scenarios"]["stale_scan"]["passed"] = False
            self.assertFalse(m3.evaluate(behavior, passing_graph(), responses, root).passed)


if __name__ == "__main__":
    unittest.main()
