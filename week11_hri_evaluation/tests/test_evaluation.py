import unittest
from app import sample_trials
from evaluation.contracts import baseline_requirements,prototype_requirements,redesign_requirements
from evaluation.metrics import matched_comparison,summarize


class EvaluationTests(unittest.TestCase):
    def test_complete_baseline(self):
        baseline=sample_trials("baseline"); self.assertEqual(summarize(baseline)["scenario_coverage"],5); self.assertTrue(all(r.passed for r in baseline_requirements(baseline)))
    def test_privacy_gate(self):
        baseline=sample_trials("baseline"); baseline["recording_used"]=True; self.assertFalse(all(r.passed for r in baseline_requirements(baseline)))
    def test_redesign_comparison(self):
        baseline=sample_trials("baseline"); redesign=sample_trials("redesign",True); evidence={"baseline":baseline,"redesign":redesign,"design_changes":["cue","recovery"]}; comparison=matched_comparison(baseline,redesign); self.assertGreaterEqual(len(comparison["improved_metrics"]),2); self.assertTrue(all(r.passed for r in redesign_requirements(evidence)))
    def test_prototype_requires_motion_off(self):
        evidence={"observed_states":["IDLE","ANNOUNCE","APPROACH","LISTENING","CONFIRMING","ACTING","COMPLETE","ERROR"],"motion_enabled":True,"stop_tested":True,"dry_runs":2}; self.assertFalse(all(r.passed for r in prototype_requirements(evidence)))


if __name__=="__main__": unittest.main()

