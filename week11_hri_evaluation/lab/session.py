def initialize(st):
    defaults = {"stage":"intro", "student":{"name":"", "email":""}, "responses":{}, "completed_missions":[], "evidence":{}}
    for key, value in defaults.items(): st.session_state.setdefault(key, value)
def complete(st, mission, evidence):
    values = set(st.session_state["completed_missions"]); values.add(mission); st.session_state["completed_missions"] = sorted(values); st.session_state["evidence"] = {**st.session_state["evidence"], mission:evidence}

