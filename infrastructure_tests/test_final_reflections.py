from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PROMPTS = (
    "What did this activity make you think about regarding your own interests in robotics, computing, engineering, or related work?",
    "How did this activity affect your motivation to do similar kinds of work in the future?",
    "What value do you see in connecting technical or computing work with human, ethical, or societal considerations?",
    "What stood out to you about the activity, and why?",
    "Is there anything else you would like to share about your experience with the activity?",
)

LABS = (
    "week01_ros_foundations",
    "week03_motion_frames_ai",
    "week04_pid_odometry",
    "week05_sensors_uncertainty",
    "week06_slam_localization",
    "week08_vision_perception",
    "week09_planning_navigation",
    "week10_foundation_models",
    "week11_hri_evaluation",
    "week12_responsible_robotics",
    "week14_pendulum_rl",
)

MODULAR_LABS = (
    "week01_ros_foundations",
    "week03_motion_frames_ai",
    "week05_sensors_uncertainty",
    "week06_slam_localization",
    "week08_vision_perception",
    "week09_planning_navigation",
    "week10_foundation_models",
    "week11_hri_evaluation",
    "week12_responsible_robotics",
    "lab-template",
)

FINAL_PAGES = {
    "week01_ros_foundations": "pages/final.py",
    "week03_motion_frames_ai": "pages/final.py",
    "week05_sensors_uncertainty": "pages/final.py",
    "week06_slam_localization": "pages/final.py",
    "week08_vision_perception": "pages/final.py",
    "week09_planning_navigation": "pages/final.py",
    "week10_foundation_models": "pages/final_submission.py",
    "week11_hri_evaluation": "pages/final.py",
    "week12_responsible_robotics": "pages/final_submission.py",
    "lab-template": "pages/final_submission.py",
}


class FinalReflectionTests(unittest.TestCase):
    def test_canonical_instructions_preserve_every_prompt(self) -> None:
        source = (ROOT / "FINAL_REFLECTION.md").read_text(encoding="utf-8")
        self.assertIn("no more than 300 words", source)
        for prompt in PROMPTS:
            self.assertIn(prompt, source)

    def test_every_lab_readme_marks_reflection_as_required_submission(self) -> None:
        for lab in LABS:
            with self.subTest(lab=lab):
                source = (ROOT / lab / "README.md").read_text(encoding="utf-8")
                self.assertIn("## Required final reflection", source)
                self.assertIn("student_submission/final_reflection.md", source)
                self.assertIn("1–300 words", source)
                overview = (ROOT / lab / "OVERVIEW.md").read_text(encoding="utf-8")
                self.assertIn("required individual reflection", overview)
                self.assertIn("no more than 300 words", overview)

    def test_modular_labs_share_prompt_limit_and_output_contract(self) -> None:
        for lab in MODULAR_LABS:
            with self.subTest(lab=lab):
                source = (ROOT / lab / "lab" / "final_reflection.py").read_text(encoding="utf-8")
                self.assertIn("MAX_WORDS = 300", source)
                self.assertIn('path = root / "final_reflection.md"', source)
                for prompt in PROMPTS:
                    self.assertIn(prompt, source)

    def test_every_modular_final_page_gates_and_writes_reflection(self) -> None:
        for lab, relative_path in FINAL_PAGES.items():
            with self.subTest(lab=lab):
                source = (ROOT / lab / relative_path).read_text(encoding="utf-8")
                self.assertIn("render_final_reflection", source)
                self.assertIn("write_final_reflection", source)

    def test_single_file_labs_include_the_same_submission(self) -> None:
        sources = {
            "week04_pid_odometry": (ROOT / "week04_pid_odometry" / "app.py").read_text(encoding="utf-8"),
            "week14_pendulum_rl": (ROOT / "week14_pendulum_rl" / "pendulum_rl_live.py").read_text(encoding="utf-8"),
        }
        for lab, source in sources.items():
            with self.subTest(lab=lab):
                self.assertIn("final_reflection.md", source)
                for prompt in PROMPTS:
                    self.assertIn(prompt, source)
        self.assertIn("1 <= reflection_words <= 300", sources["week04_pid_odometry"])
        self.assertIn("render_final_course_reflection", sources["week14_pendulum_rl"])

    def test_shared_writer_rejects_invalid_length_and_writes_valid_response(self) -> None:
        helper_path = ROOT / "week01_ros_foundations" / "lab" / "final_reflection.py"
        fake_config = types.ModuleType("lab_config")
        fake_config.LAB = types.SimpleNamespace(submission_directory="student_submission")
        previous = sys.modules.get("lab_config")
        sys.modules["lab_config"] = fake_config
        try:
            spec = importlib.util.spec_from_file_location("tested_final_reflection", helper_path)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            if previous is None:
                sys.modules.pop("lab_config", None)
            else:
                sys.modules["lab_config"] = previous

        with self.assertRaises(ValueError):
            module.write_final_reflection(types.SimpleNamespace(session_state={"responses": {}}))
        over_limit = "word " * 301
        with self.assertRaises(ValueError):
            module.write_final_reflection(
                types.SimpleNamespace(session_state={"responses": {module.RESPONSE_KEY: over_limit}})
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            module.__file__ = str(Path(temporary_directory) / "week01" / "lab" / "final_reflection.py")
            response = "The sensor evidence changed how I think about responsible robot behavior."
            path = module.write_final_reflection(
                types.SimpleNamespace(session_state={"responses": {module.RESPONSE_KEY: response}})
            )
            self.assertEqual(path.name, "final_reflection.md")
            saved = path.read_text(encoding="utf-8")
            self.assertIn(response, saved)
            self.assertIn("_Word count: 11_", saved)


if __name__ == "__main__":
    unittest.main()
