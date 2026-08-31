from __future__ import annotations
import math, unittest
from simulation.kinematics import SEQUENCES, integrate_sequence

class KinematicsTests(unittest.TestCase):
    def test_straight_pose(self):
        pose=integrate_sequence(SEQUENCES["straight"]); self.assertAlmostEqual(pose["x"],0.45); self.assertAlmostEqual(pose["y"],0.0); self.assertAlmostEqual(pose["theta"],0.0)
    def test_turn_then_drive_pose(self):
        pose=integrate_sequence(SEQUENCES["turn_then_drive"]); self.assertAlmostEqual(pose["x"],0.0,places=6); self.assertAlmostEqual(pose["y"],0.3,places=6); self.assertAlmostEqual(pose["theta"],math.pi/2,places=6)
    def test_arc_pose(self):
        pose=integrate_sequence(SEQUENCES["arc"]); self.assertGreater(pose["x"],0.3); self.assertGreater(pose["y"],0.3)
if __name__=="__main__": unittest.main()

