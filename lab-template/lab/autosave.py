from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab_config import LAB


def submission_root() -> Path:
    return Path(__file__).resolve().parents[1] / LAB.submission_directory


def _atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def load_responses() -> dict[str, Any]:
    path = submission_root() / "autosave" / "responses.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def autosave_responses(st) -> Path:
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "student": dict(st.session_state.get("student", {})),
        "responses": dict(st.session_state.get("responses", {})),
    }
    target = submission_root() / "autosave" / "responses.json"
    _atomic_text_write(target, json.dumps(payload, indent=2, sort_keys=True))
    lines = [f"# {LAB.title} responses", ""]
    student = payload["student"]
    lines.extend([f"- Name: {student.get('name', '')}", f"- Email: {student.get('email', '')}", ""])
    for key, value in payload["responses"].items():
        lines.extend([f"## {key}", "", str(value), ""])
    _atomic_text_write(target.with_suffix(".md"), "\n".join(lines))
    return target

