import math
import unittest

from course_cmd_vel_guard.guard import bounded_values


class GuardTests(unittest.TestCase):
    def test_velocity_values_are_clamped_to_course_limits(self):
        self.assertEqual(bounded_values(0.5, -1.2, 0.22, 0.8), (0.22, -0.8))

    def test_nonfinite_velocity_is_rejected(self):
        with self.assertRaises(ValueError):
            bounded_values(math.nan, 0.0, 0.22, 0.8)


if __name__ == "__main__":
    unittest.main()
