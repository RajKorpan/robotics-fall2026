import unittest
from app import PASSING
from missions.mission_1 import MISSION
from simulation.privacy import run_privacy


class PrivacyTests(unittest.TestCase):
    def test_minimized_design_passes(self):
        result=run_privacy(PASSING["mission_1"]); self.assertEqual(result.metrics["requirements_passed"],8); self.assertTrue(MISSION.evaluate(result).passed)
    def test_raw_video_storage_fails(self):
        settings={**PASSING["mission_1"],"store_raw_video":True}; self.assertFalse(MISSION.evaluate(run_privacy(settings)).passed)
    def test_no_sensing_loses_required_utility(self):
        settings={**PASSING["mission_1"],"data_collected":"no sensing"}; self.assertLess(run_privacy(settings).metrics["task_utility"],.8)


if __name__=="__main__": unittest.main()

