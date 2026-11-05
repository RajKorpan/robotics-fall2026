import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from lab.evidence import save_progress, load_progress, save_run, saved_run, export_zip, readiness, root
from lab.drafts import checkpoint, current, capture_inputs


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"LAB9_SUBMISSION_DIR": self.temp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_restart_restores_answers_and_stage_without_losing_exact_run(self):
        state = {"stage": "mission_2", "responses": {"m1_analysis": "saved answer"}, "student": {}, "tutorial_step": 3, "tutorial_reviewed": 4, "controls": {"control_live_language_case": "clear"}}
        save_progress(state)
        self.assertEqual(load_progress()["responses"], state["responses"])
        self.assertEqual(load_progress()["stage"], "mission_2")
        save_run("mission_1", {}, [{"test": 1}], {"analysis": "response"})
        self.assertTrue(saved_run("mission_1"))

    def test_unreadable_progress_does_not_overwrite_old_file(self):
        path = root() / "autosave" / "progress_v2.json"
        path.parent.mkdir(parents=True)
        path.write_text("{broken")
        self.assertEqual(load_progress(), {})
        self.assertEqual(path.read_text(), "{broken")

    def test_zip_hashes_and_raw_model_snapshot_match(self):
        rows = [{"prompt": "Where is the mug?", "output": "Beside the laptop", "model_revision": "test revision"}]
        save_run("mission_2", {}, rows, {"analysis": "response"})
        data = export_zip()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            manifest = json.loads(archive.read("student_submission/manifest.json"))
            for name, digest in manifest["sha256"].items():
                self.assertEqual(hashlib.sha256(archive.read("student_submission/" + name)).hexdigest(), digest)
            self.assertEqual(json.loads(archive.read("student_submission/mission_2/evidence_v2.json"))["rows"], rows)
        self.assertFalse(all(row["Ready"] for row in readiness()))

    def test_replacing_a_checked_run_keeps_the_previous_snapshot(self):
        first = save_run("mission_1", {"variant": "first"}, [{"output": "original"}], {"answer": "first answer"})
        save_run("mission_1", {"variant": "second"}, [{"output": "revised"}], {"answer": "second answer"})
        prior = root() / "mission_1" / "history" / (first["run_id"] + ".json")
        self.assertEqual(json.loads(prior.read_text())["rows"], [{"output": "original"}])
        self.assertEqual(saved_run("mission_1")["settings"]["variant"], "second")

    def test_atomic_save_retries_a_temporary_file_lock(self):
        original = Path.replace
        calls = []
        def briefly_locked(path, target):
            calls.append(path)
            if len(calls) == 1:
                raise PermissionError("temporary sync lock")
            return original(path, target)
        with patch.object(Path, "replace", new=briefly_locked):
            save_progress({"stage": "intro", "responses": {"answer": "retained"}})
        self.assertEqual(len(calls), 2)
        self.assertEqual(load_progress()["responses"]["answer"], "retained")

    def test_drafts_invalidate_downstream_but_preserve_saved_evidence(self):
        state = {"responses": {"m1_analysis": "original"}, "controls": {}}
        checkpoint("mission_1", state, {}, [{"case": 1}], {})
        checkpoint("mission_2", state, {}, [{"case": 1}], {})
        checkpoint("mission_3", state, {}, [{"case": 1}], {})
        self.assertTrue(current("mission_3", state))
        state["responses"]["m1_analysis"] = "edited"
        self.assertFalse(current("mission_1", state))
        self.assertFalse(current("mission_3", state))
        self.assertTrue(saved_run("mission_1"))
        state["responses"]["m1_analysis"] = "original"
        self.assertTrue(current("mission_3", state))
        checkpoint("mission_1", state, {}, [{"case": 2}], {})
        self.assertTrue(current("mission_1", state))
        self.assertFalse(current("mission_2", state))

    def test_controls_analysis_and_identity_are_captured_before_navigation(self):
        state = {"responses": {}, "controls": {}, "response_widgets": ["m2_analysis"], "m2_analysis": "new analysis", "control_live_language_case": "ambiguous", "identity_name": "example", "identity_email": "id"}
        capture_inputs(state)
        self.assertEqual(state["responses"]["m2_analysis"], "new analysis")
        self.assertEqual(state["controls"]["control_live_language_case"], "ambiguous")
        self.assertEqual(state["student"]["email"], "id")


if __name__ == "__main__":
    unittest.main()
