import unittest
from evaluation.behavior import BehaviorConfig,DEFAULT_SCENARIOS,evaluate_scenarios
from evaluation.metrics import evaluate_rows,threshold_sweep
from missions import mission_1,mission_2,mission_3
class MissionTests(unittest.TestCase):
    def test_known_passing_evidence(self):
        names=("normal","dim","glare","far","occluded","rotated","cluttered","distractor");rows=[{"condition":name,"expected":name!="distractor","detected":name!="distractor","confidence":.8,"latency_ms":10} for name in names];metrics=evaluate_rows(rows)
        responses={**{f"mission_1.{key}":"Specific numerical and visual evidence about prediction, parameter effects, and failure causes. "*2 for key in mission_1.REFLECTIONS},**{f"mission_2.{key}":"Specific evidence about threshold tradeoffs, classical and learned comparison, and confidence limits. "*2 for key in mission_2.REFLECTIONS},**{f"mission_3.{key}":"Specific system trace, breakdown propagation, safe fallback, and deployment limitations. "*2 for key in mission_3.REFLECTIONS}}
        self.assertTrue(mission_1.evaluate({"rows":rows,"metrics":metrics},responses,4).passed);self.assertTrue(mission_2.evaluate({"rows":rows,"metrics":metrics,"threshold_sweep":threshold_sweep(rows),"selected_threshold":.5},responses,4).passed);behavior={"result":evaluate_scenarios(DEFAULT_SCENARIOS,BehaviorConfig())};self.assertTrue(mission_3.evaluate(behavior,responses,2).passed)
    def test_empty_evidence_fails(self):
        self.assertFalse(mission_1.evaluate({}, {}, 0).passed);self.assertFalse(mission_2.evaluate({}, {}, 0).passed);self.assertFalse(mission_3.evaluate({}, {}, 0).passed)
if __name__=="__main__":unittest.main()
