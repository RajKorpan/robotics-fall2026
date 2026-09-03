from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]


def evidence_root() -> Path:
    override = os.environ.get("WEEK01_EVIDENCE_ROOT")
    if override:
        return Path(override)
    return ROOT / LAB.evidence_directory


def load_json(name: str, default: Any = None) -> Any:
    path = evidence_root() / name
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {} if default is None else default


def evidence_id(*payloads: Any) -> str:
    encoded = json.dumps(payloads, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def graph_inventory(graph: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "nodes": {str(node.get("name", node)) for node in graph.get("nodes", [])},
        "topics": {str(topic.get("name", topic)) for topic in graph.get("topics", [])},
        "services": {str(service.get("name", service)) for service in graph.get("services", [])},
    }


def latest_graph() -> dict[str, Any]:
    return load_json("graph_snapshot.json", {})


def motion_trials() -> list[dict[str, Any]]:
    payload = load_json("motion_trials.json", [])
    return payload if isinstance(payload, list) else payload.get("trials", [])


def behavior_evaluation() -> dict[str, Any]:
    return load_json("behavior_evaluation.json", {})


def preflight_result() -> dict[str, Any]:
    return load_json("preflight.json", {})
