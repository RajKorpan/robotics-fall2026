import unittest

from course_lab_tools.timed_twist import timing_metrics


class TimingMetricsTests(unittest.TestCase):
    def test_timing_metrics_compare_requested_and_actual_duration(self):
        metrics = timing_metrics(3.0, 10.0, 13.04, -0.2)
        self.assertAlmostEqual(metrics["actual_command_duration"], 3.04)
        self.assertAlmostEqual(metrics["duration_error"], 0.04)
        self.assertAlmostEqual(metrics["expected_linear_travel"], 0.6)

    def test_timing_metrics_preserve_missing_timestamps(self):
        metrics = timing_metrics(2.0, None, None, 0.1)
        self.assertIsNone(metrics["actual_command_duration"])
        self.assertIsNone(metrics["duration_error"])
        self.assertAlmostEqual(metrics["expected_linear_travel"], 0.2)
