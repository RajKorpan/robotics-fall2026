from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab_config import LAB
from lab.session import sanitize_responses


ROOT = Path(__file__).resolve().parents[1]


def submission_root() -> Path:
    return ROOT / LAB.submission_directory


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def load_saved_state() -> dict[str, Any]:
    path = submission_root() / "autosave" / "responses.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def autosave(st) -> Path:
    raw_student = dict(st.session_state.get("student", {}))
    student = {key: str(raw_student.get(key, "")) for key in ("name", "email")}
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "student": student,
        "responses": sanitize_responses(dict(st.session_state.get("responses", {}))),
        "completed_missions": list(st.session_state.get("completed_missions", [])),
        "checked_evidence_ids": dict(st.session_state.get("checked_evidence_ids", {})),
    }
    target = submission_root() / "autosave" / "responses.json"
    _atomic_write(target, json.dumps(payload, indent=2, sort_keys=True))
    lines = [f"# {LAB.title}", "", "## Student", ""]
    for key, value in payload["student"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    for key, value in sorted(payload["responses"].items()):
        lines.extend(["", f"## {key}", "", str(value)])
    _atomic_write(target.with_suffix(".md"), "\n".join(lines) + "\n")
    (submission_root() / "student.json").write_text(
        json.dumps(payload["student"], indent=2), encoding="utf-8"
    )
    return target
