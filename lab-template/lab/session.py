from __future__ import annotations

from typing import Any

from lab_config import LAB
from lab.models import RunResult


def initialize_session(st) -> None:
    defaults: dict[str, Any] = {
        "stage": LAB.stages[0],
        "active_mission": LAB.missions[0],
        "completed_missions": [],
        "latest_runs": {},
        "checked_run_ids": {},
        "responses": {},
        "student": {"name": "", "email": ""},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def set_response(st, key: str, value: str) -> None:
    responses = dict(st.session_state.get("responses", {}))
    responses[key] = value
    st.session_state["responses"] = responses


def store_run(st, result: RunResult) -> None:
    runs = dict(st.session_state.get("latest_runs", {}))
    runs[result.mission_id] = result
    st.session_state["latest_runs"] = runs
    checked = dict(st.session_state.get("checked_run_ids", {}))
    checked.pop(result.mission_id, None)
    st.session_state["checked_run_ids"] = checked


def mark_checked(st, result: RunResult) -> None:
    checked = dict(st.session_state.get("checked_run_ids", {}))
    checked[result.mission_id] = result.run_id
    st.session_state["checked_run_ids"] = checked


def mark_complete(st, mission_id: str) -> None:
    completed = list(st.session_state.get("completed_missions", []))
    if mission_id not in completed:
        completed.append(mission_id)
    st.session_state["completed_missions"] = completed
    index = LAB.missions.index(mission_id)
    if index + 1 < len(LAB.missions):
        st.session_state["active_mission"] = LAB.missions[index + 1]

