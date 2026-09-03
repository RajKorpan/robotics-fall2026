from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(AppTest is not None, "Streamlit is available in the course container")
class StreamlitPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.submission_directory = tempfile.TemporaryDirectory()
        cls.evidence_directory = tempfile.TemporaryDirectory()
        cls.previous_submission_root = os.environ.get("WEEK01_SUBMISSION_ROOT")
        cls.previous_evidence_root = os.environ.get("WEEK01_EVIDENCE_ROOT")
        os.environ["WEEK01_SUBMISSION_ROOT"] = cls.submission_directory.name
        os.environ["WEEK01_EVIDENCE_ROOT"] = cls.evidence_directory.name
        graph = {
            "captured_at": "2026-08-31T00:00:00Z",
            "nodes": [
                {"name": "/course_cmd_vel_guard"},
                {"name": "/course_evidence_collector"},
                {"name": "/ros_gz_bridge"},
                {"name": "/rviz2"},
            ],
            "topics": [
                {
                    "name": name,
                    "types": [message_type],
                    "publishers": ["/node_0"] if name in ("/scan", "/odom") else ["/node_2"] if name == "/cmd_vel" else [],
                    "subscribers": ["/node_1"] if name in ("/scan", "/odom") else ["/node_2"] if name == "/student_cmd_vel" else ["/node_3"],
                }
                for name, message_type in {
                    "/scan": "sensor_msgs/msg/LaserScan",
                    "/odom": "nav_msgs/msg/Odometry",
                    "/student_cmd_vel": "geometry_msgs/msg/Twist",
                    "/cmd_vel": "geometry_msgs/msg/TwistStamped",
                }.items()
            ],
            "samples": {},
        }
        (Path(cls.evidence_directory.name) / "graph_snapshot.json").write_text(
            json.dumps(graph), encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.previous_submission_root is None:
            os.environ.pop("WEEK01_SUBMISSION_ROOT", None)
        else:
            os.environ["WEEK01_SUBMISSION_ROOT"] = cls.previous_submission_root
        if cls.previous_evidence_root is None:
            os.environ.pop("WEEK01_EVIDENCE_ROOT", None)
        else:
            os.environ["WEEK01_EVIDENCE_ROOT"] = cls.previous_evidence_root
        cls.submission_directory.cleanup()
        cls.evidence_directory.cleanup()

    def test_every_stage_renders_without_exception(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"))
        app.run(timeout=20)
        self.assertFalse(app.exception)
        for stage in (
            "part_1",
            "part_2",
            "part_3",
            "preflight",
            "mission_1",
            "mission_2",
            "mission_3",
            "final",
        ):
            with self.subTest(stage=stage):
                app.session_state["stage"] = stage
                app.run(timeout=20)
                self.assertFalse(app.exception)

    def test_part_one_continue_unlocks_after_three_comparisons(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"))
        app.run(timeout=20)
        app.session_state["stage"] = "part_1"
        app.session_state["responses"] = {
            "part_1.activity": {
                example: {"normal": True, "changed": True}
                for example in ("sensor", "timing", "hardware")
            }
        }
        app.run(timeout=20)
        button = next(item for item in app.button if item.label == "Continue to Part 2")
        self.assertFalse(button.disabled)

    def test_part_two_continue_unlocks_after_five_comparisons(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"))
        app.run(timeout=20)
        app.session_state["stage"] = "part_2"
        app.session_state["responses"] = {
            "part_2.activity": {
                example: {"normal": True, "changed": True}
                for example in ("reactive", "behavior", "deliberative", "hybrid", "safety")
            }
        }
        app.run(timeout=20)
        button = next(item for item in app.button if item.label == "Continue to Part 3")
        self.assertFalse(button.disabled)

    def test_part_three_continue_unlocks_after_all_observations(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"))
        app.run(timeout=20)
        app.session_state["stage"] = "part_3"
        app.session_state["responses"] = {
            "part_3.activity": {
                "middleware": {"single": True, "multiple": True},
                "communication": {"topic": True, "service": True},
                "failure": {"healthy": True, "sensor": True, "type": True, "visualization": True},
                "inspection": {
                    item: True
                    for item in ("nodes", "node_info", "topics", "topic_info", "echo", "services", "broken")
                },
            }
        }
        app.run(timeout=20)
        button = next(item for item in app.button if item.label == "Continue to environment preflight")
        self.assertFalse(button.disabled)


if __name__ == "__main__":
    unittest.main()
