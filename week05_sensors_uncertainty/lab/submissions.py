from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from lab.autosave import submission_root
from lab_config import LAB
from simulation.plotting import png_bytes


def _json_ready(value):
    if isinstance(value, float) and (value == float("inf") or value == float("-inf")):
        return "infinity"
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def save_mission(mission_id: str, evidence: dict, responses: dict, *, rows=None, figure=None) -> Path:
    target = submission_root() / mission_id
    target.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "lab_id": LAB.id, "mission_id": mission_id, "saved_at": datetime.now(timezone.utc).isoformat(), "evidence": _json_ready(evidence)}
    (target / "submission.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if rows:
        with (target / "measurements.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    if figure is not None:
        (target / "evidence.png").write_bytes(png_bytes(figure))
    prefix = f"{mission_id}."
    lines = [f"# {mission_id.replace('_', ' ').title()}", ""]
    for key, value in sorted(responses.items()):
        if key.startswith(prefix): lines.extend([f"## {key[len(prefix):].replace('_', ' ').title()}", "", str(value), ""])
    (target / "explanation.md").write_text("\n".join(lines), encoding="utf-8")
    return target


def write_manifest(st) -> Path:
    root = submission_root(); root.mkdir(parents=True, exist_ok=True)
    files = sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file() and path.name != "manifest.json")
    payload = {"schema_version": 1, "lab_id": LAB.id, "generated_at": datetime.now(timezone.utc).isoformat(), "student": dict(st.session_state.get("student", {})), "completed_missions": list(st.session_state.get("completed_missions", [])), "files": files}
    path = root / "manifest.json"; path.write_text(json.dumps(payload, indent=2), encoding="utf-8"); return path
