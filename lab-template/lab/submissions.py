from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.autosave import submission_root
from lab.models import MissionCheck, RunResult
from lab_config import LAB


def trace_csv(result: RunResult) -> str:
    if not result.traces:
        return ""
    columns = list(result.traces)
    length = max((len(values) for values in result.traces.values()), default=0)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(columns)
    for index in range(length):
        writer.writerow([result.traces[column][index] if index < len(result.traces[column]) else "" for column in columns])
    return stream.getvalue()


def save_mission(result: RunResult, check: MissionCheck, explanations: dict[str, str]) -> Path:
    target = submission_root() / result.mission_id
    target.mkdir(parents=True, exist_ok=True)
    payload = result.serializable()
    payload.update({
        "schema_version": 1,
        "lab_id": LAB.id,
        "passed": check.passed,
        "requirements": [requirement.__dict__ for requirement in check.requirements],
    })
    (target / "latest_run.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (target / "submission.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    explanation_lines = [f"# {result.mission_id} explanations", ""]
    for key, answer in explanations.items():
        explanation_lines.extend([f"## {key}", "", answer, ""])
    (target / "explanation.md").write_text("\n".join(explanation_lines), encoding="utf-8")
    (target / "run.csv").write_text(trace_csv(result), encoding="utf-8")
    for name, contents in result.artifacts.items():
        artifact = target / "activity_gifs" / name
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(contents)
    return target


def write_manifest(st) -> Path:
    root = submission_root()
    root.mkdir(parents=True, exist_ok=True)
    files = sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file())
    payload: dict[str, Any] = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student": dict(st.session_state.get("student", {})),
        "completed_missions": list(st.session_state.get("completed_missions", [])),
        "checked_run_ids": dict(st.session_state.get("checked_run_ids", {})),
        "files": files,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path

