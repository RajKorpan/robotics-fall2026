"""Keep dependency fixes and retired-instruction handling consistent."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "week11_hri_evaluation"


class SetupRecoveryTests(unittest.TestCase):
    def test_all_install_paths_use_the_arm64_build_fix(self):
        for name in (ROOT/"docker/requirements.txt", LAB/"requirements.txt"):
            text=name.read_text(encoding="utf-8")
            self.assertIn("pocketsphinx==5.1.0",text)
            self.assertNotIn("pocketsphinx==5.0.4",text)
        text=(LAB/"scripts/course_preflight.sh").read_text(encoding="utf-8")
        self.assertIn('version("pocketsphinx") == "5.1.0"',text)
        self.assertIn("pip install -r requirements.txt",text)
        self.assertIn("make_decoder()",text)
        self.assertIn("libportaudio2",(ROOT/"docker/Dockerfile").read_text())

    def test_retired_script_explains_current_workflow_without_starting_old_demo(self):
        text=(LAB/"scripts/launch_interaction.sh").read_text(encoding="utf-8")
        self.assertIn("launch_handover.sh",text)
        self.assertIn("microphone",text)
        self.assertIn("student_submission",text)
        self.assertIn("exit 2",text)
        self.assertNotIn("ros2 topic pub",text)
        self.assertNotIn("ros2 launch",text)
