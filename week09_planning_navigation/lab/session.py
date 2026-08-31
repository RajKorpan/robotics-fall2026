def initialize(st):
    defaults = {"stage": "intro", "student": {"name": "", "email": ""}, "responses": {}, "completed_missions": [], "evidence": {}}
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value


def complete_mission(st, mission, evidence):
    completed = set(st.session_state["completed_missions"]); completed.add(mission)
    st.session_state["completed_missions"] = sorted(completed); st.session_state["evidence"] = {**st.session_state["evidence"], mission: evidence}

