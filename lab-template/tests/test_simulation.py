from __future__ import annotations

import unittest

from simulation.core import simulate_feedback
from simulation.metrics import feedback_metrics


class SimulationTests(unittest.TestCase):
    def test_feedback_trace_has_aligned_columns(self) -> None:
        trace = simulate_feedback(gain=1.0, target=1.0)
        lengths = {len(values) for values in trace.values()}
        self.assertEqual(lengths, {161})

    def test_feedback_reduces_error(self) -> None:
        trace = simulate_feedback(gain=1.0, target=1.0)
        metrics = feedback_metrics(trace)
        self.assertLess(metrics["final_error"], abs(trace["error"][0]))


if __name__ == "__main__":
    unittest.main()

