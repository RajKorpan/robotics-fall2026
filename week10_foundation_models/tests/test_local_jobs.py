import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab.evidence import root, read_json, write_json, atomic
from lab.local_jobs import start_job, job_status, cancel_job, records_complete, queue_path
from tests.live_fixtures import fixture_runs


class LocalJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.patches = [patch.dict(os.environ, {"LAB9_SUBMISSION_DIR": str(self.base / "submission")}),
                        patch("lab.local_jobs.queue_path", side_effect=lambda kind: self.base / kind),
                        patch("lab.local_jobs.installed", return_value=True), patch("lab.local_jobs._ensure_worker"),
                        patch("lab.local_jobs._workers", {})]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_live_completion_is_persisted_without_replacing_raw_response(self):
        job = start_job("language", "clear", "A request")
        queue = self.base / "language"
        request = read_json(queue / (job + ".request.json"))
        response = {"status": "complete", "record": {**request, "output": "Actual result from a test double"}}
        write_json(queue / (job + ".result.json"), response)
        self.assertEqual(job_status("language", job), response)
        self.assertEqual(read_json(root() / "mission_1" / "attempts" / (job + ".result.json")), response)

    def test_cancel_and_error_do_not_become_completed_experiments(self):
        job = start_job("language", "clear", "A request")
        cancel_job("language", job)
        self.assertEqual(job_status("language", job)["status"], "cancelled")
        job2 = start_job("language", "clear", "Another request")
        write_json(self.base / "language" / (job2 + ".result.json"), {"status": "error", "error": "Model error"})
        self.assertEqual(job_status("language", job2)["status"], "error")
        self.assertFalse(records_complete("mission_1", []))

    def test_input_images_are_saved_exactly_and_preflight_does_not_fill_submission(self):
        job = start_job("vision", "identify", "A question")
        from lab.local_config import scene_path
        self.assertEqual((root() / "mission_2" / "attempts" / (job + ".jpg")).read_bytes(), scene_path("identify").read_bytes())
        probe = start_job("language", "clear", "Say ready", "preflight")
        self.assertFalse((root() / "mission_1" / "attempts" / (probe + ".request.json")).exists())
        write_json(self.base / "language" / (probe + ".result.json"), {"status": "complete", "record": {"output": "Ready"}})
        job_status("language", probe)
        self.assertFalse((root() / "mission_1" / "attempts" / (probe + ".result.json")).exists())

    def test_all_cases_and_a_changed_matched_prompt_are_required_not_accuracy(self):
        rows = fixture_runs("language")
        self.assertTrue(records_complete("mission_1", rows))
        self.assertFalse(records_complete("mission_1", rows[:3]))
        self.assertFalse(records_complete("mission_1", rows[1:]))
        unchanged = copy.deepcopy(rows)
        unchanged[-1]["prompt"] = unchanged[0]["prompt"]
        self.assertFalse(records_complete("mission_1", unchanged))
        wrong_parent = copy.deepcopy(rows)
        wrong_parent[-1]["comparison_ids"] = [rows[1]["job_id"]]
        self.assertFalse(records_complete("mission_1", wrong_parent))
        for row in rows:
            row["output"] = "An incorrect but nonempty model answer"
        self.assertTrue(records_complete("mission_1", rows))

    def test_missing_or_changed_model_outputs_cannot_count_as_live_evidence(self):
        rows = fixture_runs("vision")
        self.assertTrue(records_complete("mission_2", rows))
        rows[1]["live_inference"] = False
        self.assertFalse(records_complete("mission_2", rows))
        rows[1]["live_inference"] = True
        rows[-1]["image_sha256"] = "changed image"
        self.assertFalse(records_complete("mission_2", rows))

    def test_robot_jobs_are_saved_under_mission_three_and_keep_the_state_snapshot(self):
        from simulation.robot_room import initial_state
        job = start_job("language", "goal", "Reach the target.", robot_state=initial_state())
        request = read_json(self.base / "language" / (job + ".request.json"))
        self.assertEqual(request["robot_state"], initial_state())
        self.assertEqual(request["task"], "robot")
        self.assertTrue((root() / "mission_3" / "attempts" / (job + ".request.json")).exists())
        write_json(self.base / "language" / (job + ".result.json"), {"status": "complete", "record": {**request, "output": "UP"}})
        job_status("language", job)
        self.assertTrue((root() / "mission_3" / "attempts" / (job + ".result.json")).exists())
        self.assertFalse((root() / "mission_1" / "attempts" / (job + ".result.json")).exists())


if __name__ == "__main__":
    unittest.main()
