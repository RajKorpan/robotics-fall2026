from lab.navigation import set_stage
from missions import MISSIONS
def render(st):
    st.header("Policy sandbox"); mission_id=st.selectbox("Explore system",list(MISSIONS),format_func=lambda x:MISSIONS[x].title); mission=MISSIONS[mission_id]; settings=mission.render_controls(st)
    if st.button("Run sandbox configuration",type="primary"):
        result=mission.run(settings); st.session_state["sandbox.result"]=result; st.session_state["sandbox.mission"]=mission_id
    result=st.session_state.get("sandbox.result")
    if result and st.session_state.get("sandbox.mission")==mission_id: st.dataframe(result.traces,hide_index=True,width="stretch"); st.json(result.metrics)
    st.caption("Sandbox results are not submitted. Save a checked run inside each mission.")
    if st.button("Start Mission 1"): set_stage(st,"lab")

