from __future__ import annotations
import os, unittest
from week03_pattern.pattern import Segment, build_pattern

class PatternTests(unittest.TestCase):
    def setUp(self): self.name=os.environ.get("WEEK03_ASSIGNED_PATTERN","l_path"); self.segments=build_pattern(self.name)
    def test_nonempty(self): self.assertGreaterEqual(len(self.segments),3)
    def test_segment_types(self): self.assertTrue(all(isinstance(item,Segment) for item in self.segments))
    def test_positive_durations(self): self.assertTrue(all(item.duration>0 for item in self.segments))
    def test_linear_limits(self): self.assertTrue(all(abs(item.linear_x)<=0.22 for item in self.segments))
    def test_angular_limits(self): self.assertTrue(all(abs(item.angular_z)<=0.8 for item in self.segments))
    def test_pattern_contains_motion(self): self.assertTrue(any(item.linear_x or item.angular_z for item in self.segments))
    def test_pattern_contains_turning(self): self.assertTrue(any(abs(item.angular_z)>0 for item in self.segments))
if __name__=="__main__": unittest.main()

