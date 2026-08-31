import unittest
from pathlib import Path


class StructureTests(unittest.TestCase):
    def test_template_boundaries(self):
        root=Path(__file__).resolve().parents[1]
        for name in ("lab","missions","pages","simulation","student_submission"): self.assertTrue((root/name).is_dir())


if __name__=="__main__": unittest.main()
