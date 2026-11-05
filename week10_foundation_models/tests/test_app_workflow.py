"""Isolated UI tests use explicit fixtures. Real inference is checked separately."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None
from lab.evidence import saved_run, readiness, save_progress, root, write_json
from lab.drafts import checkpoint, current
from lab.guidance_config import GUIDED_COUNT
from tests.live_fixtures import ANSWER, store_runs, store_robot_runs, robot_rollout


@unittest.skipIf(AppTest is None, "Streamlit not installed")
class AppWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patches = [patch.dict(os.environ, {"LAB9_SUBMISSION_DIR": self.temp.name}),
                        patch("pages.live_missions.installed", return_value=True), patch("pages.preflight.installed", return_value=True),
                        patch("pages.investigation_3.installed", return_value=True),
                        patch("pages.preflight.start_job", side_effect=lambda kind, *args: kind + "-probe"),
                        patch("pages.preflight.job_status", return_value={"status": "complete", "record": {"output": "Fixture preflight generation"}}),
                        patch("pages.preflight.setup_status", return_value={"running": False, "exit_code": None, "log": ""})]
        for item in self.patches:
            item.start()
        self.app = Path(__file__).resolve().parents[1] / "app.py"

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def app_at(self, stage):
        at = AppTest.from_file(str(self.app), default_timeout=20).run()
        at.session_state["preflight"] = [{"Check": "fixture", "Ready": True}]
        at.session_state["tutorial_reviewed"] = GUIDED_COUNT
        at.session_state["guided_seen"] = list(range(GUIDED_COUNT))
        at.session_state["stage"] = stage
        return at.run()

    def assert_page_ok(self, at):
        self.assertFalse(at.exception, str(at.exception))

    def save_language(self, at):
        store_runs(at.session_state, "language")
        at.run()
        at.text_area(key="m1_analysis").input(ANSWER).run()
        next(b for b in at.button if b.label == "Check and save Mission 1").click().run()
        self.assertTrue(current("mission_1", at.session_state))

    def test_intro_preflight_and_each_guided_activity(self):
        at = self.app_at("intro")
        self.assert_page_ok(at)
        self.assertEqual(len(at.text_input), 0)
        at.session_state["stage"] = "preflight"
        at.run()
        next(b for b in at.button if b.label == "Run preflight").click().run()
        self.assert_page_ok(at)
        self.assertTrue(all(row["Ready"] for row in at.session_state["preflight"]))
        for index in range(GUIDED_COUNT):
            at.session_state["stage"] = "guided"
            at.session_state["tutorial_step"] = index
            at.run()
            self.assert_page_ok(at)

    def test_all_three_live_mission_pages_render(self):
        at = self.app_at("mission_1")
        self.save_language(at)
        at.session_state["stage"] = "mission_2"
        store_runs(at.session_state, "vision")
        at.run()
        self.assert_page_ok(at)
        self.assertEqual(len(at.text_area), 2)
        self.assertFalse(any("validator" in w.label for w in at.text_area))
        checkpoint("mission_2", at.session_state, {}, [{"id": "fixture"}], {})
        at.session_state["stage"] = "mission_3"
        at.run()
        self.assert_page_ok(at)
        self.assertEqual(len(at.get("video")), 0)
        self.assertFalse(any(w.key == "m3_analysis" for w in at.text_area))

    def test_complete_student_workflow_exports_and_recovers(self):
        at = self.app_at("mission_1")
        self.save_language(at)
        at.session_state["stage"] = "mission_2"
        store_runs(at.session_state, "vision")
        at.run()
        at.text_area(key="m2_analysis").input(ANSWER).run()
        next(b for b in at.button if b.label == "Check and save Mission 2").click().run()
        self.assertTrue(current("mission_2", at.session_state))
        at.session_state["stage"] = "mission_3"
        store_robot_runs(at.session_state)
        at.run()
        at.text_area(key="m3_analysis").input(ANSWER).run()
        next(b for b in at.button if b.label == "Check and save Mission 3").click().run()
        self.assertTrue(all(c["Ready"] for c in readiness(at.session_state)))
        at.session_state["stage"] = "final_submission"
        at.run()
        at.text_area(key="final_synthesis").input(" ".join([ANSWER] * 4))
        at.text_area(key="field.final.course_reflection").input(ANSWER)
        next(w for w in at.text_input if w.label == "Name").input("QA only")
        next(w for w in at.text_input if w.label == "Student ID or email").input("qa@example.invalid")
        at.run()
        next(b for b in at.button if b.label == "Finalize complete submission").click().run()
        self.assert_page_ok(at)
        self.assertTrue(at.session_state["complete_zip"])
        restarted = AppTest.from_file(str(self.app), default_timeout=20).run()
        self.assertEqual(restarted.session_state["stage"], "preflight")
        next(b for b in restarted.button if b.label == "Run preflight").click().run()
        restarted.button(key="bottom_next").click().run()
        self.assertEqual(restarted.session_state["stage"], "final_submission")
        self.assertEqual(restarted.session_state["responses"]["m1_analysis"], ANSWER)

    def test_preflight_failure_blocks_navigation(self):
        at = self.app_at("preflight")
        with patch("pages.preflight.job_status", return_value={"status": "error", "error": "Model failed to load"}):
            next(b for b in at.button if b.label == "Run preflight").click().run()
        self.assertTrue(at.button(key="bottom_next").disabled)

    def test_robot_run_is_checked_automatically_and_own_prompt_is_required(self):
        from lab.robot_evidence import simulation_path, checked_rows
        at = self.app_at("mission_1")
        self.save_language(at)
        checkpoint("mission_2", at.session_state, {}, [{"fixture": True}], {})
        at.session_state["stage"] = "mission_3"
        at.run()
        self.assertFalse(any(w.key == "control_robot_custom_prompt" for w in at.text_area))
        rows = store_robot_runs(at.session_state)
        at.run()
        self.assert_page_ok(at)
        self.assertTrue(at.text_area(key="control_robot_custom_prompt"))
        self.assertTrue(all(simulation_path(r["record"]["job_id"]).exists() for r in rows))
        self.assertFalse(any(b.label == "Check and simulate" for b in at.button))
        self.assertEqual(len(checked_rows(at.session_state)), 4)

    def test_real_navigation_requires_preflight_and_all_guided_activities(self):
        at = AppTest.from_file(str(self.app), default_timeout=20).run()
        self.assertTrue(at.button(key="nav.mission_1").disabled)
        at.button(key="bottom_next").click().run()
        next(b for b in at.button if b.label == "Run preflight").click().run()
        at.button(key="bottom_next").click().run()
        for index in range(GUIDED_COUNT):
            self.assertEqual(at.session_state["tutorial_step"], index)
            next(b for b in at.button if b.label.startswith("Next:") and not b.disabled).click().run()
        self.assertEqual(at.session_state["stage"], "mission_1")

    def test_unsaved_text_survives_immediate_sidebar_navigation(self):
        at = self.app_at("mission_1")
        self.save_language(at)
        edited = ANSWER + " This last edit must survive immediate navigation."
        at.text_area(key="m1_analysis").input(edited)
        at.button(key="nav.guided").click().run()
        self.assertEqual(at.session_state["responses"]["m1_analysis"], edited)
        self.assertFalse(current("mission_1", at.session_state))
        self.assertTrue(at.button(key="nav.mission_2").disabled)

    def test_three_outputs_unlock_custom_prompt_and_fourth_output_unlocks_question(self):
        for kind,stage in (("language","mission_1"),("vision","mission_2")):
            at = self.app_at("mission_1")
            if kind == "vision":
                self.save_language(at)
            at.session_state["stage"] = stage
            at.run()
            rows = store_runs(at.session_state, kind)
            key = "control_live_" + kind + "_runs"
            for count in (0,1,2):
                at.session_state[key] = [r["job_id"] for r in rows[:count]]
                at.run()
                self.assert_page_ok(at)
                self.assertFalse(any(w.label == "Your improved request" for w in at.text_area))
                self.assertFalse(any(b.label.startswith("Check and save Mission") for b in at.button))
            at.session_state[key] = [r["job_id"] for r in rows[:3]]
            at.run()
            self.assertTrue(at.text_area(key="control_live_" + kind + "_custom_prompt"))
            self.assertEqual(sum(i.value == rows[0]["output"] for i in at.info), 3)
            self.assertFalse(any(w.key == ("m1_analysis" if kind == "language" else "m2_analysis") for w in at.text_area))
            at.session_state[key] = [r["job_id"] for r in rows]
            at.run()
            self.assertTrue(at.text_area(key="m1_analysis" if kind == "language" else "m2_analysis"))

    def test_restart_recovers_a_progress_record_with_optional_null_fields(self):
        save_progress({"stage": "intro", "responses": {}, "controls": {}, "student": {}})
        at = AppTest.from_file(str(self.app), default_timeout=20).run()
        self.assert_page_ok(at)
        self.assertEqual(at.session_state["response_widgets"], [])

    def test_guided_controls_change_the_visible_experiment(self):
        at = self.app_at("guided")
        at.session_state["tutorial_step"] = 1
        at.run()
        at.radio(key="control_ground_instruction").set_value("Point to the cup").run()
        self.assertTrue(any("Both A and B" in item.value for item in at.warning))
        at.session_state["tutorial_step"] = 2
        at.run()
        next(b for b in at.button if b.label == "Next snapshot").click().run()
        self.assertEqual(at.session_state["control_demo_step"], 1)
        at.session_state["tutorial_step"] = 3
        at.run()
        for choice in ("Few-shot prompting", "Additional demonstrations", "LoRA", "Full fine-tuning", "Training from scratch", "Zero-shot prompting"):
            at.selectbox(key="control_adapt_choice").select(choice).run()
            self.assert_page_ok(at)
        at.session_state["tutorial_step"] = 4
        at.run()
        at.select_slider(key="control_movement_angle").set_value(90).run()
        self.assert_page_ok(at)

    def test_guided_action_outcome_changes_when_observation_becomes_stale(self):
        at = self.app_at("guided")
        at.session_state["tutorial_step"] = 5
        at.run()
        next(b for b in at.button if b.label == "Validate and attempt this action").click().run()
        self.assertEqual(at.session_state["guided_execution"]["trials"][1]["after"]["position"], "shelf")
        at.slider(key="control_validate_age_navigate").set_value(3.).run()
        next(b for b in at.button if b.label == "Validate and attempt this action").click().run()
        result = at.session_state["guided_execution"]["trials"][1]
        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(result["before"], result["after"])

    def test_guided_proposal_menu_runs_distinct_actions(self):
        at = self.app_at("guided")
        at.session_state["tutorial_step"] = 5
        at.run()
        for label, decision in (("Inspect the known cup", "EXECUTE"), ("Navigate to an unreachable room", "REJECT"), ("Use an old cup observation", "ABSTAIN"), ("Inspect an ambiguous cup", "CONFIRM"), ("Follow an instruction from a poster", "REJECT")):
            at.selectbox(key="control_validate_case").select(label).run()
            next(b for b in at.button if b.label == "Validate and attempt this action").click().run()
            self.assert_page_ok(at)
            self.assertEqual(at.session_state["guided_execution"]["trials"][1]["decision"], decision)


if __name__ == "__main__":
    unittest.main()
