import unittest
from evaluation.behavior import BehaviorConfig,DEFAULT_SCENARIOS,decide,evaluate_scenarios
from evaluation.metrics import conditions_complete,evaluate_rows,threshold_sweep
class EvaluationTests(unittest.TestCase):
    def test_perception_metrics(self):
        rows=[{"condition":name,"expected":name!="distractor","detected":name not in ("far","distractor"),"confidence":.8,"latency_ms":10} for name in ("normal","dim","glare","far","occluded","rotated","cluttered","distractor")];metrics=evaluate_rows(rows)
        self.assertTrue(conditions_complete(rows));self.assertEqual(metrics["tp"],6);self.assertEqual(len(threshold_sweep(rows)),5)
    def test_behavior_safety_and_states(self):
        result=evaluate_scenarios(DEFAULT_SCENARIOS,BehaviorConfig());self.assertTrue(result["passed"]);self.assertEqual(decide(None,1,BehaviorConfig())["state"],"STOP")
    def test_low_confidence_never_approaches(self):
        command=decide({"detected":True,"confidence":.2,"center_offset":0,"area_fraction":.1},.1,BehaviorConfig());self.assertEqual(command["linear_x"],0)
if __name__=="__main__":unittest.main()
