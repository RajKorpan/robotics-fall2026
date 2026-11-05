"""Directional movement checks and replayable prompt-comparison evidence."""
import copy
import os
import tempfile
import unittest
from unittest.mock import patch
from simulation.robot_room import START, GOAL, WALLS, COMMAND_OPTIONS, initial_state, route, parse_command, evaluate, summarize
from tests.live_fixtures import robot_model, robot_rollout, store_robot_runs
from lab.robot_evidence import complete, compatible, checked_rows, simulation_path


class RobotRoomTests(unittest.TestCase):
    def test_map_needs_a_detour_but_has_a_feasible_route(self):
        path = route(START, GOAL)
        self.assertEqual(len(path)-1, 28)
        self.assertTrue(all(tuple(p) not in WALLS for p in path))
        self.assertEqual(set(COMMAND_OPTIONS), {"UP","DOWN","LEFT","RIGHT","STOP"})

    def test_each_direction_changes_exactly_one_cell(self):
        for action,position in (("UP",[1,6]),("RIGHT",[2,7])):
            before = initial_state()
            result = evaluate(robot_model("goal", action), before)
            self.assertEqual(result["after"]["position"], position)
            self.assertEqual(before, initial_state())
        for action in ("DOWN","LEFT"):
            result = evaluate(robot_model("goal", action), initial_state())
            self.assertEqual(result["decision"], "BLOCKED")
            self.assertEqual(result["after"]["position"], START)
            self.assertTrue(result["after"]["finished"])

    def test_stop_invalid_prose_and_stale_state_do_not_move(self):
        for action in ("STOP", "I suggest UP", "UP DOWN", "__import__('os')"):
            result = evaluate(robot_model("goal",action), initial_state())
            self.assertEqual(result["after"]["position"], START)
            self.assertTrue(result["after"]["finished"])
        model = robot_model("goal","UP")
        state = initial_state()
        state["position"] = [2,7]
        self.assertEqual(evaluate(model,state)["decision"],"BLOCKED")
        self.assertIsNone(parse_command("UP then RIGHT"))

    def test_replay_reaches_goal_without_a_hidden_route_controller(self):
        actions = ["UP"]*6 + ["RIGHT"]*6 + ["DOWN"]*6 + ["RIGHT"]*4 + ["UP"]*6
        model = robot_rollout("goal",actions)
        receipt = summarize(model)
        self.assertTrue(receipt["goal_reached"])
        self.assertEqual(receipt["moves"],28)
        self.assertEqual(receipt["after"]["position"],GOAL)
        changed = copy.deepcopy(model)
        changed["steps"][2]["simulation"]["after"]["position"] = GOAL
        with self.assertRaises(ValueError):
            summarize(changed)

    def test_three_originals_and_a_new_own_prompt_are_required(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,{"LAB9_SUBMISSION_DIR":folder}):
            state = {"controls":{}}
            rows = store_robot_runs(state)
            self.assertTrue(complete(rows,verify_files=True))
            self.assertFalse(complete(rows[:3]))
            self.assertFalse(complete(rows[1:]))
            changed = copy.deepcopy(rows)
            changed[-1]["record"]["comparison_ids"] = []
            changed[-1]["simulation"] = summarize(changed[-1]["record"])
            self.assertFalse(complete(changed))
            model = copy.deepcopy(rows[0]["record"])
            model["steps"][0]["model"]["model_input"] = "tampered state"
            self.assertFalse(compatible(model))
            simulation_path(rows[0]["record"]["job_id"]).unlink()
            self.assertEqual(len(checked_rows(state)),4)
            self.assertTrue(simulation_path(rows[0]["record"]["job_id"]).exists())


if __name__ == "__main__":
    unittest.main()
