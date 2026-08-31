from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]


def evidence_root() -> Path:
    return ROOT / LAB.evidence_directory


def load_json(name: str, default: Any = None) -> Any:
    path = evidence_root() / name
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {} if default is None else default


def evidence_id(*values: Any) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def preflight() -> dict[str, Any]:
    return load_json("preflight.json", {})


def motion_runs() -> list[dict[str, Any]]:
    payload = load_json("motion_sequences.json", [])
    return payload if isinstance(payload, list) else payload.get("runs", [])


def frame_snapshot() -> dict[str, Any]:
    return load_json("frame_snapshot.json", {})


def ai_evaluation() -> dict[str, Any]:
    return load_json("ai_evaluation.json", {})

