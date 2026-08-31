from __future__ import annotations

import unittest

from missions import MISSIONS


class MissionTests(unittest.TestCase):
    def test_every_mission_has_requirements(self) -> None:
        settings = {
            "gain": 2.0,
            "target": 1.0,
            "disturbance": -0.2,
            "sensor_noise": 0.05,
        }
        for mission in MISSIONS.values():
            with self.subTest(mission=mission.id):
                result = mission.run(settings)
                check = mission.evaluate(result)
                self.assertEqual(result.mission_id, mission.id)
                self.assertTrue(check.requirements)

    def test_mission_one_known_configuration_passes(self) -> None:
        mission = MISSIONS["mission_1"]
        result = mission.run({"gain": 1.0, "target": 1.0, "disturbance": 0.0, "sensor_noise": 0.0})
        self.assertTrue(mission.evaluate(result).passed)


if __name__ == "__main__":
    unittest.main()

