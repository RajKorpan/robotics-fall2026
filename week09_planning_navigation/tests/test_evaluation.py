import unittest
from evaluation.contracts import human_aware_requirements, navigation_requirements, plan_requirements
from evaluation.metrics import path_length, summarize_plans, summarize_trials


class EvaluationTests(unittest.TestCase):
    def test_path_length(self): self.assertAlmostEqual(path_length([{"x": 0, "y": 0}, {"x": 3, "y": 4}]), 5)
    def test_plan_contract(self):
        rows = [{"goal_id": k, "expected_reachable": e, "status": "succeeded" if e else "failed", "waypoint_count": 3 if e else 0, "path_length_m": 1 if e else 0, "minimum_clearance_m": .2 if e else None} for k, e in (("open_short", 1), ("detour", 1), ("narrow", 1), ("occupied_goal", 0), ("blocked_goal", 0))]
        self.assertTrue(all(r.passed for r in plan_requirements({"rows": rows})))
    def test_navigation_contract_rejects_collision(self):
        rows = [{"condition": c, "status": "succeeded", "collision_events": int(i == 0)} for i, c in enumerate(("open", "narrow", "unexpected_obstacle", "open", "unexpected_obstacle"))]
        checks = navigation_requirements({"rows": rows}); self.assertFalse(all(r.passed for r in checks))
    def test_human_aware_comparison(self):
        evidence = {"policy": {"required_clearance_m": .75, "maximum_nearby_speed_mps": .12}, "baseline": {"scenario_id": "s", "goal_id": "g", "metrics": {"minimum_person_clearance_m": .1}}, "redesign": {"scenario_id": "s", "goal_id": "g", "status": "succeeded", "metrics": {"minimum_person_clearance_m": .8, "maximum_speed_near_people_mps": .1}}, "parameter_changes": ["mask", "speed"]}
        self.assertTrue(all(r.passed for r in human_aware_requirements(evidence)))


if __name__ == "__main__": unittest.main()
