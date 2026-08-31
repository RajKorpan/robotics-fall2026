import unittest
from app import PASSING
from missions.mission_2 import MISSION
from simulation.fairness import run_fairness


class FairnessTests(unittest.TestCase):
    def test_intervention_passes_bounded_requirements(self):
        result=run_fairness(PASSING["mission_2"]); self.assertTrue(MISSION.evaluate(result).passed); self.assertEqual(result.metrics["samples"],32)
    def test_threshold_alone_does_not_fix_performance(self):
        result=run_fairness({"threshold":.55,"intervention":"none","abstain_margin":0.0,"human_review":False}); self.assertFalse(MISSION.evaluate(result).passed); self.assertGreater(result.metrics["tpr_gap"],.2)
    def test_baseline_is_preserved_for_comparison(self):
        result=run_fairness(PASSING["mission_2"]); self.assertIn("baseline_without_intervention",result.metrics); self.assertGreater(result.metrics["baseline_without_intervention"]["tpr_gap"],result.metrics["tpr_gap"])


if __name__=="__main__": unittest.main()

