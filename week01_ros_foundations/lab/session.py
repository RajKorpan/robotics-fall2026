from __future__ import annotations

from typing import Any


TUTORIAL_ACTIVITY_KEYS = {"part_1.activity", "part_2.activity", "part_3.activity"}
RETIRED_MISSION_2_KEYS = {
    "mission_2.predictions_locked_at",
    "mission_2.target_plan",
    "mission_2.target_reached",
    "mission_2.command_path",
    "mission_2.velocity_vs_destination",
    "mission_2.combined_velocity",
    "mission_2.least_accurate",
    "mission_2.command_vs_motion",
    "mission_2.safe_stop",
    "mission_2.timing_evidence",
    "mission_2.delay_risk",
    "mission_2.stale_command",
}


def sanitize_responses(values: dict[str, Any]) -> dict[str, Any]:
    """Discard fields from the retired quiz-style versions of Parts 1–3."""
    return {
        key: value
        for key, value in values.items()
        if (not key.startswith(("part_1.", "part_2.", "part_3.")) or key in TUTORIAL_ACTIVITY_KEYS)
        and key not in RETIRED_MISSION_2_KEYS
    }


def initialize_session(st) -> None:
    defaults: dict[str, Any] = {
        "stage": "intro",
        "student": {"name": "", "email": ""},
        "responses": {},
        "completed_missions": [],
        "checked_evidence_ids": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    saved_student = dict(st.session_state.get("student", {}))
    st.session_state["student"] = {
        "name": str(saved_student.get("name", "")),
        "email": str(saved_student.get("email", "")),
    }
    st.session_state["responses"] = sanitize_responses(dict(st.session_state.get("responses", {})))


def response(st, key: str, default: Any = "") -> Any:
    return st.session_state.get("responses", {}).get(key, default)


def set_response(st, key: str, value: Any) -> None:
    responses = dict(st.session_state.get("responses", {}))
    responses[key] = value
    st.session_state["responses"] = responses


def complete_mission(st, mission_id: str, evidence_id: str) -> None:
    completed = list(st.session_state.get("completed_missions", []))
    if mission_id not in completed:
        completed.append(mission_id)
    st.session_state["completed_missions"] = completed
    checked = dict(st.session_state.get("checked_evidence_ids", {}))
    checked[mission_id] = evidence_id
    st.session_state["checked_evidence_ids"] = checked
