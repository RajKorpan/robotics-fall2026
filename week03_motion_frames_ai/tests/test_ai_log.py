from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from lab.ai_log import assigned_pattern, load_lock, lock_original

class AssignmentTests(unittest.TestCase):
    def test_assignment_is_deterministic(self): self.assertEqual(assigned_pattern("abc123"),assigned_pattern("abc123"))
    def test_assignment_is_supported(self): self.assertIn(assigned_pattern("student"),{"rounded_rectangle","l_path","alternating_arcs"})
    def test_locked_output_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch("lab.ai_log.submission_root",return_value=root):
                lock_original("student","specification","prompt","original output")
                self.assertTrue(load_lock()["integrity_valid"])
                (root/"mission_3"/"ai"/"original_output.txt").write_text("changed",encoding="utf-8")
                self.assertFalse(load_lock()["integrity_valid"])
if __name__=="__main__": unittest.main()
