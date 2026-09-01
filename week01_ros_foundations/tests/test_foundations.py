from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

from lab import submissions
from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]


class FoundationIntegrationTests(unittest.TestCase):
    def test_required_parts_precede_preflight_and_missions(self) -> None:
        self.assertEqual(
            LAB.stages,
            ("intro", "part_1", "part_2", "part_3", "preflight", "mission_1", "mission_2", "mission_3", "final"),
        )

    def test_three_parts_cover_slide_concepts(self) -> None:
        expected = {
            "part_1.py": ("Sensors", "Timing", "Distribution", "Hardware"),
            "part_2.py": ("Reactive", "Behavior-based", "Deliberative", "Hybrid", "Layered safety"),
            "part_3.py": ("middleware", "Node", "Topic", "Message", "Service", "ROS graph"),
        }
        for filename, concepts in expected.items():
            with self.subTest(page=filename):
                source = (ROOT / "pages" / filename).read_text(encoding="utf-8")
                for concept in concepts:
                    self.assertIn(concept, source)

    def test_foundations_and_diagram_are_durable_artifacts(self) -> None:
        responses = {
            "part_1.challenge_one": "A delayed response can create a collision.",
            "part_2.lab_prediction": "Reactive",
            "part_3.middleware": "ROS 2 connects components.",
            "mission_1.node_roles": {"/laser": "Sensing"},
            "mission_1.pipeline_roles": {"/laser": "Sense"},
            "mission_1.service_example": {
                "name": "/reset_world",
                "type": "std_srvs/srv/Empty",
                "purpose": "Reset the simulation",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = submissions.submission_root
            submissions.submission_root = lambda: root
            try:
                path = submissions.write_foundations_summary(
                    types.SimpleNamespace(session_state={"responses": responses})
                )
            finally:
                submissions.submission_root = previous
            self.assertEqual(path, root / "foundations.md")
            summary = path.read_text(encoding="utf-8")
            self.assertIn("Why robotics software is difficult", summary)
            self.assertIn("Robot software architectures", summary)
            self.assertIn("What ROS 2 provides", summary)

            diagram = submissions._write_ros_system_diagram(root / "mission_1", responses)
            rendered = diagram.read_text(encoding="utf-8")
            self.assertIn("/student_cmd_vel", rendered)
            self.assertIn("/reset_world", rendered)
            self.assertIn("Sense–decide–act role", rendered)

    def test_collector_records_services_and_timing_tool_records_stop(self) -> None:
        collector = (
            ROOT / "ros2_ws" / "src" / "course_evidence_collector" /
            "course_evidence_collector" / "collector.py"
        ).read_text(encoding="utf-8")
        timed_twist = (
            ROOT / "ros2_ws" / "src" / "course_lab_tools" /
            "course_lab_tools" / "timed_twist.py"
        ).read_text(encoding="utf-8")
        self.assertIn("get_service_names_and_types", collector)
        for field in (
            "command_started_at",
            "zero_command_sent_at",
            "actual_command_duration",
            "duration_error",
            "expected_linear_travel",
        ):
            self.assertIn(field, timed_twist)


if __name__ == "__main__":
    unittest.main()
