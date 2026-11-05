"""Versioned exact-run evidence, atomic writes, restart recovery and ZIP exports."""
from __future__ import annotations

import hashlib
import csv
import io
import json
import os
import uuid
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = 2
ROOT = Path(__file__).resolve().parents[1]


def root():
    return Path(os.environ.get("LAB9_SUBMISSION_DIR", ROOT / "student_submission"))


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_bytes(data)
    # File sync and virus scanners can briefly hold a Windows destination open.
    # Keep the atomic operation and retry instead of falling back to a partial write.
    for attempt in range(5):
        try:
            temp.replace(path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(.025 * (2 ** attempt))


def write_json(path, data):
    if path.exists():
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            atomic(path.with_name(path.name + ".unreadable." + uuid.uuid4().hex + ".bak"), path.read_bytes())
    atomic(path, (json.dumps(data, indent=2, allow_nan=False) + "\n").encode())


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_progress(state):
    data = {key: state.get(key) for key in ("stage", "responses", "student", "tutorial_step", "tutorial_reviewed", "controls", "guided_version", "guided_seen", "response_widgets")}
    data["version"] = VERSION
    write_json(root() / "autosave" / "progress_v2.json", data)


def load_progress():
    data = read_json(root() / "autosave" / "progress_v2.json", {})
    if data.get("version") == VERSION:
        return data
    legacy = read_json(root() / "autosave" / "responses.json", {})
    return {"responses": legacy.get("responses", {}), "student": legacy.get("student", {}), "stage": "intro"} if legacy else {}


def save_run(mission, settings, rows, responses, extra=None):
    if mission not in ("mission_1", "mission_2", "mission_3"):
        raise ValueError(mission)
    payload = {"version": VERSION, "run_id": uuid.uuid4().hex, "mission": mission,
               "saved_at": datetime.now(timezone.utc).isoformat(), "settings": settings,
               "rows": rows, "responses": responses, "extra": extra or {}}
    path = root() / mission / "evidence_v2.json"
    previous = read_json(path, {})
    if previous.get("run_id"):
        # Preserve checked results when a revised run replaces the latest snapshot.
        history_id = "".join(c for c in str(previous["run_id"]) if c.isalnum())
        write_json(path.parent / "history" / (history_id + ".json"), previous)
    write_json(path, payload)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    table = io.StringIO(newline="")
    writer = csv.DictWriter(table, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value for key, value in row.items()})
    atomic(path.parent / "run.csv", table.getvalue().encode())
    for key, value in responses.items():
        atomic(path.parent / (key + ".md"), value.encode())
    return payload


def saved_run(mission):
    data = read_json(root() / mission / "evidence_v2.json", {})
    return data if data.get("version") == VERSION else {}


def readiness(state=None):
    from lab.drafts import current
    state = load_progress() if state is None else state
    checks = []
    for mission in ("mission_1", "mission_2", "mission_3"):
        data = saved_run(mission)
        rows = data.get("rows", [])
        complete = bool(rows) and all(len(str(value).split()) >= 15 for value in data.get("responses", {}).values())
        if mission in ("mission_1", "mission_2"):
            from lab.local_jobs import records_complete
            complete = complete and data.get("settings", {}).get("experiment") == "local-live-v2" and records_complete(mission, rows)
            for row in rows:
                raw = read_json(root() / mission / "attempts" / (str(row.get("job_id")) + ".result.json"), {})
                complete = complete and raw.get("record") == row and raw.get("status") == "complete"
                if mission == "mission_2":
                    photo = root() / mission / "attempts" / (str(row.get("job_id")) + ".jpg")
                    complete = complete and photo.is_file() and hashlib.sha256(photo.read_bytes()).hexdigest() == row.get("image_sha256")
        else:
            from lab.robot_evidence import complete as robot_complete
            complete = complete and data.get("settings", {}).get("experiment") == "local-robot-v4" and robot_complete(rows, verify_files=True)
        checks.append({"Requirement": mission.replace("_", " ").title() + " current evidence saved", "Ready": bool(complete and current(mission, state)), "Next action": "Saved and current" if complete and current(mission, state) else "Review changes and Check and save " + mission.replace("_", " ")})
    return checks


def export_zip():
    paths = sorted(p for p in root().rglob("*") if p.is_file() and p.name not in (".gitkeep", "manifest.json") and ".tmp" not in p.name and "__pycache__" not in p.parts)
    hashes = {p.relative_to(root()).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    write_json(root() / "manifest.json", {"version": VERSION, "sha256": hashes, "generated_at": datetime.now(timezone.utc).isoformat()})
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths + [root() / "manifest.json"]:
            archive.write(path, "student_submission/" + path.relative_to(root()).as_posix())
    return buffer.getvalue()
