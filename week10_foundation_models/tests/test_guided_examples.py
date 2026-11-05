import unittest
import copy
import xml.etree.ElementTree as ET
from pathlib import Path

from simulation.guided_examples import audio_envelope, region_matches, demonstration_records, decoded_movement, chunk_trial, decision_walkthrough
from simulation.guided_validation import CASES, STATE, reference_validate, execute
from pages.guided_visuals import execution_result_svg


class GuidedExamplesTests(unittest.TestCase):
    def test_region_matching_preserves_ambiguity(self):
        self.assertEqual(region_matches("Point to the blue cup"), ["A"])
        self.assertEqual(region_matches("Point to the red cup"), ["B"])
        self.assertEqual(region_matches("Point to the cup"), ["A", "B"])

    def test_demonstration_links_result_to_next_observation(self):
        rows = demonstration_records()
        for row in rows:
            self.assertAlmostEqual(row["Observed x (m)"] + row["Forward command (m/s)"] * row["Held for (s)"], row["Resulting x (m)"])
        for first, following in zip(rows, rows[1:]):
            self.assertEqual(first["Resulting x (m)"], following["Observed x (m)"])
        self.assertEqual(rows[-1]["Forward command (m/s)"], 0)

    def test_frame_rotation_changes_direction_not_distance(self):
        aligned = decoded_movement(191, 0)
        rotated = decoded_movement(191, 90)
        self.assertAlmostEqual(rotated["world_dx_m"], 0)
        self.assertAlmostEqual(aligned["world_dx_m"], rotated["world_dy_m"])
        self.assertLess(decoded_movement(30, 0)["world_dx_m"], 0)

    def test_chunk_control_changes_reaction_and_path(self):
        baseline, delay_one = chunk_trial(1, 10)
        held, delay_four = chunk_trial(4, 10)
        self.assertEqual(delay_one, 0)
        self.assertEqual(delay_four, .3)
        self.assertNotEqual(baseline[6]["y_m"], held[6]["y_m"])
        _, faster = chunk_trial(4, 20)
        self.assertLess(faster, delay_four)

    def test_explained_decisions_match_guided_policy(self):
        for _, proposal, expected in CASES:
            verdict, trace = decision_walkthrough(proposal)
            self.assertEqual(verdict, expected)
            self.assertEqual(verdict, reference_validate(proposal, STATE))
            stopping = [i for i, row in enumerate(trace) if row["Result"] in ("REJECT", "ABSTAIN", "CONFIRM")]
            if stopping:
                self.assertTrue(all(row["Result"] == "Not reached" for row in trace[stopping[0]+1:]))

    def test_audio_plot_is_derived_from_bundled_speech(self):
        path = Path(__file__).resolve().parents[1] / "assets" / "guided" / "stop_robot.wav"
        duration, peaks = audio_envelope(path)
        self.assertGreater(duration, .5)
        self.assertGreater(max(peaks), 0)
        self.assertLessEqual(max(peaks), 1)

    def test_execution_images_represent_each_proposal_and_its_actual_effect(self):
        pictures = {}
        for case_id, proposal, _ in CASES:
            if case_id not in ("navigate", "inspect", "unreachable", "stale", "ambiguous", "poster"):
                continue
            verdict, _ = decision_walkthrough(proposal)
            state = copy.deepcopy(STATE)
            success, feedback = execute(proposal, state) if verdict == "EXECUTE" else (False, "No execution. " + verdict)
            result = {"before": copy.deepcopy(STATE), "after": state, "decision": verdict, "completed": success, "feedback": feedback}
            picture = execution_result_svg(proposal, result)
            ET.fromstring(picture)
            pictures[case_id] = picture
            if verdict != "EXECUTE":
                self.assertEqual(state, STATE)
                self.assertIn("Withheld: " + verdict, picture)
        self.assertEqual(len(set(pictures.values())), 6)
        self.assertIn('marker-end="url(#move-tip)"', pictures["navigate"])
        self.assertIn("Fresh inspection recorded", pictures["inspect"])
        self.assertIn("No new inspection", pictures["stale"])
        self.assertIn("which cup?", pictures["ambiguous"])
        self.assertIn("Source: environment", pictures["poster"])
        self.assertIn("closed_room", pictures["unreachable"])


if __name__ == "__main__":
    unittest.main()
