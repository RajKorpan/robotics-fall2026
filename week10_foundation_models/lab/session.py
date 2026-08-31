from lab_config import LAB


def initialize_session(st):
    defaults = {"stage": LAB.stages[0], "active_mission": LAB.missions[0], "completed_missions": [], "latest_runs": {}, "checked_run_ids": {}, "responses": {}, "student": {"name": "", "email": ""}}
    for key, value in defaults.items(): st.session_state.setdefault(key, value)


def set_response(st, key, value):
    responses = dict(st.session_state.get("responses", {})); responses[key] = value; st.session_state["responses"] = responses


def store_run(st, result):
    runs = dict(st.session_state["latest_runs"]); runs[result.mission_id] = result; st.session_state["latest_runs"] = runs
    checked = dict(st.session_state["checked_run_ids"]); checked.pop(result.mission_id, None); st.session_state["checked_run_ids"] = checked


def mark_checked(st, result):
    checked = dict(st.session_state["checked_run_ids"]); checked[result.mission_id] = result.run_id; st.session_state["checked_run_ids"] = checked


def mark_complete(st, mission_id):
    completed = list(st.session_state["completed_missions"])
    if mission_id not in completed: completed.append(mission_id)
    st.session_state["completed_missions"] = completed
    index = LAB.missions.index(mission_id)
    if index + 1 < len(LAB.missions): st.session_state["active_mission"] = LAB.missions[index + 1]

