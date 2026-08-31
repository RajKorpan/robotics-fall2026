from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.autosave import submission_root
from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]


def save_mission(mission_id: str, evidence: dict[str, Any], responses: dict[str, Any]) -> Path:
    target = submission_root() / mission_id
    target.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "mission_id": mission_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "evidence": evidence,
    }
    (target / "submission.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (target / "latest_run.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    prefix = f"{mission_id}."
    answers = {key[len(prefix):]: value for key, value in responses.items() if key.startswith(prefix)}
    lines = [f"# {mission_id.replace('_', ' ').title()}", ""]
    for key, value in answers.items():
        lines.extend([f"## {key.replace('_', ' ').title()}", "", str(value), ""])
    (target / "explanation.md").write_text("\n".join(lines), encoding="utf-8")
    return target


def snapshot_student_source() -> Path:
    source = ROOT / "ros2_ws" / "src" / "week01_behavior"
    target = submission_root() / "mission_3" / "source"
    target.mkdir(parents=True, exist_ok=True)
    for relative in (
        "package.xml",
        "setup.py",
        "setup.cfg",
        "week01_behavior/decision.py",
        "week01_behavior/obstacle_guard.py",
        "test/test_decision.py",
    ):
        source_file = source / relative
        if source_file.exists():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
    return target


def write_manifest(st) -> Path:
    root = submission_root()
    root.mkdir(parents=True, exist_ok=True)
    files = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student": dict(st.session_state.get("student", {})),
        "completed_missions": list(st.session_state.get("completed_missions", [])),
        "checked_evidence_ids": dict(st.session_state.get("checked_evidence_ids", {})),
        "files": files,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path

