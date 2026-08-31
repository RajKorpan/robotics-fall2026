from __future__ import annotations

import math
import unittest

from week01_behavior.decision import decide_velocity, front_distance


class DecisionTests(unittest.TestCase):
    def test_clear_path_moves(self) -> None:
        self.assertEqual(decide_velocity(2.0, 0.5, 0.08), 0.08)

    def test_close_obstacle_stops(self) -> None:
        self.assertEqual(decide_velocity(0.3, 0.5, 0.08), 0.0)

    def test_threshold_stops(self) -> None:
        self.assertEqual(decide_velocity(0.5, 0.5, 0.08), 0.0)

    def test_missing_measurement_stops(self) -> None:
        self.assertEqual(decide_velocity(None, 0.5, 0.08), 0.0)

    def test_front_sector_ignores_invalid_values(self) -> None:
        ranges = [0.1, math.inf, 0.8, math.nan, 0.6, math.inf, 0.1]
        measured = front_distance(ranges, -0.3, 0.1, 0.15)
        self.assertAlmostEqual(measured, 0.6)

    def test_empty_front_sector_is_missing(self) -> None:
        measured = front_distance([math.inf] * 7, -0.3, 0.1, 0.15)
        self.assertIsNone(measured)

    def test_forward_output_is_not_amplified(self) -> None:
        self.assertLessEqual(decide_velocity(2.0, 0.5, 0.08), 0.08)


if __name__ == "__main__":
    unittest.main()

