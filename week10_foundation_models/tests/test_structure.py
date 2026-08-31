import json, unittest
from pathlib import Path


class StructureTests(unittest.TestCase):
    def test_scenario_ids_are_unique(self):
        root = Path(__file__).resolve().parents[1] / "assets" / "scenarios"
        for path in root.glob("*.json"):
            rows = json.loads(path.read_text(encoding="utf-8")); ids = [r["id"] for r in rows]; self.assertEqual(len(ids), len(set(ids)), path.name)
    def test_template_boundaries_exist(self):
        root = Path(__file__).resolve().parents[1]
        for folder in ("lab", "missions", "pages", "simulation", "student_submission"): self.assertTrue((root / folder).is_dir())


if __name__ == "__main__": unittest.main()
