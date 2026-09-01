from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

from lab import submissions
from lab.navigation import set_stage
from lab.session import initialize_session, sanitize_responses
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
            "robotics_challenges": ("Sensor", "Timing", "Distributed system", "Hardware"),
            "architecture_playground": ("Reactive", "Behavior-based", "Deliberative", "Hybrid", "Safety override"),
            "ros_graph_playground": ("Middleware", "Node", "Topic", "Message", "Service", "graph"),
        }
        for component, concepts in expected.items():
            with self.subTest(component=component):
                source = (ROOT / "components" / component / "index.html").read_text(encoding="utf-8")
                for concept in concepts:
                    self.assertIn(concept, source)
                self.assertIn("streamlit:setComponentValue", source)

    def test_foundation_pages_are_demonstrations_not_quizzes(self) -> None:
        forbidden = ("text_response", "choice_response", "selectbox", "text_area", "number_input")
        for number in (1, 2, 3):
            source = (ROOT / "pages" / f"part_{number}.py").read_text(encoding="utf-8")
            for term in forbidden:
                self.assertNotIn(term, source)
            self.assertIn("tutorial_component", source)

    def test_foundations_and_diagram_are_durable_artifacts(self) -> None:
        responses = {
            "part_1.activity": {"sensor": True, "timing": True, "distributed": True, "hardware": True},
            "part_2.activity": {"modes": {"reactive": True, "hybrid": True}, "safety": True},
            "part_3.activity": {"topic": True, "service": True, "failure": True, "inspect": True},
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
            self.assertIn("ungraded", summary)
            self.assertIn("Why robotics software is difficult", summary)
            self.assertIn("Robot software architectures", summary)
            self.assertIn("What ROS 2 provides", summary)

            diagram = submissions._write_ros_system_diagram(root / "mission_1", responses)
            rendered = diagram.read_text(encoding="utf-8")
            self.assertIn("/student_cmd_vel", rendered)
            self.assertIn("/reset_world", rendered)
            self.assertIn("Sense–decide–act role", rendered)

    def test_identity_and_retired_quiz_fields_are_sanitized(self) -> None:
        class FakeStreamlit:
            def __init__(self) -> None:
                self.session_state = {
                    "student": {"name": "Student", "email": "student@example.edu", "course_id": "old"},
                    "responses": {"part_1.challenge_one": "old", "mission_1.note": "keep"},
                }

            def rerun(self) -> None:
                self.reran = True

        fake = FakeStreamlit()
        initialize_session(fake)
        self.assertEqual(set(fake.session_state["student"]), {"name", "email"})
        self.assertEqual(sanitize_responses(fake.session_state["responses"]), {"mission_1.note": "keep"})
        set_stage(fake, "part_1")
        self.assertTrue(fake.session_state["scroll_to_top_pending"])
        self.assertTrue(fake.reran)

    def test_course_id_is_removed_from_student_interface(self) -> None:
        for relative in ("pages/intro.py", "lab/session.py", "lab/autosave.py", "lab/submissions.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("Course ID", source)

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
