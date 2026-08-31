import unittest
from app import PASSING
from missions.mission_3 import MISSION
from simulation.policy import run_policy


class PolicyTests(unittest.TestCase):
    def test_complete_policy_passes(self): self.assertTrue(MISSION.evaluate(run_policy(PASSING["mission_3"])).passed)
    def test_continue_fallback_fails(self):
        settings={**PASSING["mission_3"],"fallback":"continue last action"}; result=run_policy(settings); self.assertGreater(result.metrics["unsafe_scenarios"],0); self.assertFalse(MISSION.evaluate(result).passed)
    def test_single_feedback_mode_fails_access_scenarios(self):
        settings={**PASSING["mission_3"],"audio_feedback":False,"physical_stop":False}; self.assertFalse(MISSION.evaluate(run_policy(settings)).passed)


if __name__=="__main__": unittest.main()

