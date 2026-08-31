from __future__ import annotations

from typing import Any


def initialize(st) -> None:
    defaults: dict[str, Any] = {
        "stage": "intro",
        "student": {"name": "", "email": "", "course_id": ""},
        "responses": {},
        "completed_missions": [],
        "checked_evidence_ids": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def response(st, key: str, default: Any = "") -> Any:
    return st.session_state.get("responses", {}).get(key, default)


def set_response(st, key: str, value: Any) -> None:
    payload = dict(st.session_state.get("responses", {}))
    payload[key] = value
    st.session_state["responses"] = payload


def complete_mission(st, mission_id: str, evidence_id: str) -> None:
    completed = list(st.session_state.get("completed_missions", []))
    if mission_id not in completed:
        completed.append(mission_id)
    st.session_state["completed_missions"] = completed
    checked = dict(st.session_state.get("checked_evidence_ids", {}))
    checked[mission_id] = evidence_id
    st.session_state["checked_evidence_ids"] = checked

