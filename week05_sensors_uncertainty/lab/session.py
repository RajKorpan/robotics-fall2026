from __future__ import annotations
from typing import Any
def initialize(st):
    defaults:dict[str,Any]={"stage":"intro","student":{"name":"","email":"","course_id":""},"responses":{},"completed_missions":[],"checked_evidence_ids":{},"mission_2_attempts":[],"mission_3_results":{}}
    for key,value in defaults.items(): st.session_state.setdefault(key,value)
def response(st,key,default=""): return st.session_state.get("responses",{}).get(key,default)
def set_response(st,key,value):
    payload=dict(st.session_state.get("responses",{})); payload[key]=value; st.session_state["responses"]=payload
def complete_mission(st,mission_id,evidence_id):
    completed=list(st.session_state.get("completed_missions",[]));
    if mission_id not in completed: completed.append(mission_id)
    st.session_state["completed_missions"]=completed; checked=dict(st.session_state.get("checked_evidence_ids",{})); checked[mission_id]=evidence_id; st.session_state["checked_evidence_ids"]=checked

