import json
import unittest
from pathlib import Path


class StructureTests(unittest.TestCase):
    def test_current_mission_boundaries_exist(self):
        root = Path(__file__).resolve().parents[1]
        for folder in ("lab", "pages", "simulation", "student_submission"):
            self.assertTrue((root / folder).is_dir())

    def test_guided_recording_has_required_attribution(self):
        folder = Path(__file__).resolve().parents[1] / "assets" / "policy_recordings"
        sources = json.loads((folder / "sources.json").read_text())
        self.assertEqual([item["id"] for item in sources], ["cup_reattempt"])
        clip = folder / sources[0]["file"]
        self.assertIn(b"ftyp", clip.read_bytes()[:40])
        self.assertTrue(sources[0]["url"].startswith("https://openvla.github.io/"))
        self.assertFalse(sources[0]["raw_actions_available"])


if __name__ == "__main__":
    unittest.main()
