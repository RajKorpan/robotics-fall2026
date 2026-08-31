from lab_config import LAB
def initialize_session(st):
    defaults={"stage":LAB.stages[0],"active_mission":LAB.missions[0],"completed_missions":[],"latest_runs":{},"checked_run_ids":{},"responses":{},"student":{"name":"","email":""}}
    for key,value in defaults.items(): st.session_state.setdefault(key,value)
def set_response(st,key,value): values=dict(st.session_state["responses"]); values[key]=value; st.session_state["responses"]=values
def store_run(st,result): values=dict(st.session_state["latest_runs"]); values[result.mission_id]=result; st.session_state["latest_runs"]=values; checked=dict(st.session_state["checked_run_ids"]); checked.pop(result.mission_id,None); st.session_state["checked_run_ids"]=checked
def mark_checked(st,result): values=dict(st.session_state["checked_run_ids"]); values[result.mission_id]=result.run_id; st.session_state["checked_run_ids"]=values
def mark_complete(st,mission_id):
    values=list(st.session_state["completed_missions"])
    if mission_id not in values: values.append(mission_id)
    st.session_state["completed_missions"]=values; index=LAB.missions.index(mission_id)
    if index+1<len(LAB.missions): st.session_state["active_mission"]=LAB.missions[index+1]

