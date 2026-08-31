import math
import unittest

from simulation.filters import median_filter, moving_average
from simulation.scenarios import fusion_dataset, run_pipeline
from simulation.sensors import SensorConfig, sample_metrics, static_samples


class SimulationTests(unittest.TestCase):
    def test_sensor_runs_are_repeatable(self):
        config = SensorConfig(noise_std=.1, dropout_rate=.1, outlier_rate=.1)
        self.assertEqual(static_samples(2.0, 40, config, 17), static_samples(2.0, 40, config, 17))

    def test_statistics_use_valid_samples(self):
        metrics = sample_metrics([1.0, None, 2.0, 3.0], 2.0)
        self.assertEqual(metrics["valid_count"], 3)
        self.assertEqual(metrics["dropout_count"], 1)
        self.assertAlmostEqual(metrics["mean"], 2.0)
        self.assertAlmostEqual(metrics["variance"], 1.0)

    def test_filters_handle_missing_values(self):
        self.assertEqual(moving_average([1.0, None, 3.0], 2), [1.0, 1.0, 2.0])
        self.assertEqual(median_filter([1.0, 9.0, 2.0], 3)[-1], 2.0)

    def test_pipeline_returns_finite_metrics(self):
        result = run_pipeline(fusion_dataset(42), "Median", 3, .35, .5)
        self.assertTrue(all(math.isfinite(value) for value in result["metrics"].values()))
        self.assertEqual(len(result["estimate"]), len(result["filtered_a"]))


if __name__ == "__main__": unittest.main()
