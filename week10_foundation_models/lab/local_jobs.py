"""Nonblocking jobs, persisted attempts, cancellation and model setup status."""
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
import threading
from datetime import datetime, timezone

from lab.evidence import ROOT, root, write_json, read_json, atomic
from lab.local_config import MODEL_CONFIG, LANGUAGE_TASKS, LANGUAGE_SYSTEM, VISION_TASKS, VISION_PREPROCESSING, model_python, model_dir, scene_path

_workers = {}
_setup = None
_worker_lock = threading.Lock()


def installed():
    return model_python().is_file() and all(read_json(model_dir(k) / "course_model.json", {}) == v for k, v in MODEL_CONFIG.items())


def setup_status(start=False):
    global _setup
    log = ROOT / "runtime" / "local_model_setup.log"
    if start and (_setup is None or _setup.poll() is not None):
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w") as output:
            _setup = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "setup_local_models.py")], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    return {"running": _setup is not None and _setup.poll() is None, "exit_code": _setup.poll() if _setup else None,
            "log": log.read_text(errors="replace")[-7000:] if log.exists() else ""}


def queue_path(kind):
    return ROOT / "runtime" / "inference_queue" / kind


def _ensure_worker(kind):
    with _worker_lock:
        worker = _workers.get(kind)
        if worker is None or worker.poll() is not None:
            queue = queue_path(kind)
            queue.mkdir(parents=True, exist_ok=True)
            env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false"}
            with (queue / "worker.log").open("a") as log:
                _workers[kind] = subprocess.Popen([str(model_python()), "-m", "lab.local_inference", kind, str(queue)], cwd=ROOT,
                                                  env=env, stdout=log, stderr=subprocess.STDOUT)


def start_job(kind, case, prompt, phase="baseline", parent_id=None, robot_state=None, comparison_ids=None):
    if not installed():
        raise ValueError("Prepare the local models on Preflight first.")
    if robot_state is not None:
        from simulation.robot_room import SCENARIOS
        if kind != "language":
            raise ValueError("Robot proposals use the local language model.")
        choices = {**SCENARIOS, "custom": {}}
    else:
        choices = LANGUAGE_TASKS if kind == "language" else VISION_TASKS
        choices = {**choices, "custom": {}}
    if case not in choices or not 1 <= len(prompt.strip()) <= 1200:
        raise ValueError("Choose a supplied case and a prompt containing 1 to 1200 characters.")
    job_id = uuid.uuid4().hex
    mission = "mission_3" if robot_state is not None else "mission_1" if kind == "language" else "mission_2"
    request = {"job_id": job_id, "kind": kind, "case": case, "prompt": prompt.strip(), "phase": phase,
               "parent_id": parent_id, "requested_at": datetime.now(timezone.utc).isoformat()}
    request["comparison_ids"] = comparison_ids or []
    if robot_state is not None:
        from simulation.robot_room import contract
        request.update(task="robot", robot_state=robot_state, simulator_contract=contract())
    queue = queue_path(kind)
    queue.mkdir(parents=True, exist_ok=True)
    write_json(queue / (job_id + ".request.json"), request)
    if phase != "preflight":
        write_json(root() / mission / "attempts" / (job_id + ".request.json"), request)
    if kind == "vision" and phase != "preflight":
        atomic(root() / mission / "attempts" / (job_id + ".jpg"), scene_path(case).read_bytes())
    _ensure_worker(kind)
    return job_id


def job_status(kind, job_id):
    queue = queue_path(kind)
    request = read_json(queue / (job_id + ".request.json"), {})
    result = read_json(queue / (job_id + ".result.json"), {})
    mission = "mission_3" if request.get("task") == "robot" else "mission_1" if kind == "language" else "mission_2"
    if not result:
        result = read_json(root() / mission / "attempts" / (job_id + ".result.json"), {})
        if not result and kind == "language":
            result = read_json(root() / "mission_3" / "attempts" / (job_id + ".result.json"), {})
            if result:
                mission = "mission_3"
    if result:
        destination = root() / mission / "attempts" / (job_id + ".result.json")
        if request.get("phase") != "preflight" and not destination.exists():
            write_json(destination, result)
        return result
    if (queue / (job_id + ".cancel")).exists():
        return {"status": "cancelled", "error": "This run was cancelled. You can start a new run."}
    request_path = queue / (job_id + ".request.json")
    if not request_path.exists():
        return {"status": "error", "error": "Run file is unavailable. Run this experiment again. Earlier checked evidence is retained."}
    worker = _workers.get(kind)
    if worker is not None and worker.poll() not in (None, 0):
        log = queue / "worker.log"
        failure = {"status": "error", "error": "The local model worker stopped. " + (log.read_text(errors="replace")[-1200:] if log.exists() else "Run Preflight again.")}
        write_json(queue / (job_id + ".result.json"), failure)
        return failure
    elapsed = time.time() - request_path.stat().st_mtime
    if elapsed > 300:
        cancel_job(kind, job_id)
        return {"status": "error", "error": "This run exceeded five minutes. Run it again. Check Preflight if the problem continues."}
    _ensure_worker(kind)
    return {**read_json(queue / (job_id + ".status.json"), {"status": "queued"}), "elapsed": round(elapsed, 1)}


def cancel_job(kind, job_id):
    atomic(queue_path(kind) / (job_id + ".cancel"), b"cancel")


def record(kind, job_id, mission=None):
    if not job_id:
        return None
    mission = mission or ("mission_1" if kind == "language" else "mission_2")
    result = read_json(root() / mission / "attempts" / (job_id + ".result.json"), {})
    return result.get("record") if result.get("status") == "complete" else None


def live_records(mission, state):
    kind = "language" if mission == "mission_1" else "vision"
    controls = state.get("controls", {})
    ids = state.get("control_live_" + kind + "_runs", controls.get("control_live_" + kind + "_runs", []))
    return [row for job_id in ids if (row := record(kind, job_id))]


def records_complete(mission, rows):
    kind = "language" if mission == "mission_1" else "vision"
    tasks = LANGUAGE_TASKS if kind == "language" else VISION_TASKS
    cases = set(tasks)
    good = [r for r in rows if compatible_record(kind, r)]
    baselines = {r["case"] for r in good if r.get("phase") == "baseline" and r["case"] in tasks and r.get("prompt") == tasks[r["case"]]["prompt"]}
    by_id = {r["job_id"]: r for r in good}
    revisions = [r for r in good if r.get("phase") == "custom" and r["case"] == "custom"
                 and r["prompt"] not in [t["prompt"] for t in tasks.values()]
                 and {by_id[i]["case"] for i in r.get("comparison_ids", []) if i in by_id and by_id[i].get("phase") == "baseline"} >= cases]
    return cases <= baselines and bool(revisions)


def compatible_record(kind, row):
    cases = LANGUAGE_TASKS if kind == "language" else VISION_TASKS
    if not (row.get("kind") == kind and row.get("task") != "robot" and row.get("case") in (*cases, "custom") and row.get("live_inference") is True
            and isinstance(row.get("output"), str) and row["output"].strip()
            and row.get("model") == MODEL_CONFIG[kind]["id"] and row.get("model_revision") == MODEL_CONFIG[kind]["revision"]):
        return False
    if kind == "language":
        return row.get("system_prompt") == LANGUAGE_SYSTEM
    return row.get("image_preprocessing") == VISION_PREPROCESSING and row.get("image_sha256") == hashlib.sha256(scene_path(row["case"]).read_bytes()).hexdigest()


def records_signature(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
