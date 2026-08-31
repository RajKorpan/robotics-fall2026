import unittest
from missions.mission_2 import MISSION
from simulation.vision import run_vision_suite


class VisionTests(unittest.TestCase):
    def test_standard_run_contains_scenes_and_errors(self):
        result = run_vision_suite({"confidence_threshold":.65})
        self.assertEqual(result.metrics["scenes_tested"], 8)
        self.assertEqual(len(result.artifacts), 8)
        self.assertGreater(result.metrics["unsafe_recommendations_accepted"], 0)
        self.assertTrue(MISSION.evaluate(result).passed)
    def test_high_threshold_exposes_coverage_tradeoff(self):
        low = run_vision_suite({"confidence_threshold":.3})
        high = run_vision_suite({"confidence_threshold":.9})
        self.assertLess(high.metrics["accepted_detections"], low.metrics["accepted_detections"])


if __name__ == "__main__": unittest.main()

