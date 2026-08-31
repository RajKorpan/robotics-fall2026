import unittest

from missions import mission_1, mission_2, mission_3
from simulation.scenarios import evaluate_rule, fusion_dataset, run_pipeline
from simulation.sensors import profile_for_seed, sample_metrics, static_samples


class MissionTests(unittest.TestCase):
    def test_complete_work_passes(self):
        seed = 2026; name, config = profile_for_seed(seed); metrics = sample_metrics(static_samples(2.0, 240, config, seed), 2.0)
        responses = {"mission_1.mean": metrics["mean"], "mission_1.variance": metrics["variance"], "mission_1.bias": metrics["bias"], "mission_1.median": metrics["median"], "mission_1.dropouts": metrics["dropout_count"], "mission_1.outliers": metrics["outlier_count"], "mission_1.profile": name}
        responses.update({f"mission_1.{key}": "Evidence-based explanation of measurement behavior and robot consequences. " * 2 for key in mission_1.REFLECTIONS})
        self.assertTrue(mission_1.evaluate(metrics, name, responses).passed)
        data = fusion_dataset(seed); attempts = [{"attempt": i + 1, **run_pipeline(data, method, 3, .5, .25)} for i, method in enumerate(("Moving average", "Median", "Exponential"))]
        responses.update({f"mission_2.{key}": "Measured comparison of accuracy, outliers, smoothing, fusion, and response delay. " * 2 for key in mission_2.REFLECTIONS})
        self.assertTrue(mission_2.evaluate(attempts, 1, responses).passed)
        policies = {
            "Warehouse": {"threshold": .75, "margin": .1, "weight_a": .35, "confirmations": 1, "filter_method": "Median", "window": 3, "missing_policy": "Stop"},
            "Assistive": {"threshold": .95, "margin": .2, "weight_a": .35, "confirmations": 1, "filter_method": "Median", "window": 3, "missing_policy": "Stop"},
        }
        results = {context: evaluate_rule(settings, context, seed) for context, settings in policies.items()}
        responses.update({f"mission_3.{key}": "Context-specific discussion of affected stakeholders, competing error costs, limitations, accountability, and further tests. " * 2 for key in mission_3.REFLECTIONS})
        self.assertTrue(mission_3.evaluate(results, responses).passed)

    def test_empty_work_does_not_pass(self):
        self.assertFalse(mission_2.evaluate([], -1, {}).passed)
        self.assertFalse(mission_3.evaluate({}, {}).passed)


if __name__ == "__main__": unittest.main()
