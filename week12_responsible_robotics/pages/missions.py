from lab.navigation import set_stage
from lab.session import mark_checked,mark_complete,set_response,store_run
from lab.submissions import save_mission
from lab_config import LAB
from missions import MISSIONS
def render(st):
    mission_id=st.session_state.get("active_mission",LAB.missions[0]); mission=MISSIONS[mission_id]; st.title(mission.title); st.write(mission.objective); st.caption(f"Completed: {len(st.session_state['completed_missions'])}/{len(LAB.missions)} missions")
    settings=mission.render_controls(st); signature=repr(sorted(settings.items())); key="settings."+mission_id
    if st.session_state.get(key) not in (None,signature):
        runs=dict(st.session_state["latest_runs"]); runs.pop(mission_id,None); st.session_state["latest_runs"]=runs; checked=dict(st.session_state["checked_run_ids"]); checked.pop(mission_id,None); st.session_state["checked_run_ids"]=checked
    st.session_state[key]=signature
    if st.button("Run scenario checks",type="primary",key="run."+mission_id): store_run(st,mission.run(settings))
    result=st.session_state["latest_runs"].get(mission_id)
    if result is None: st.info("Choose a design, predict its consequences, then run the checks."); return
    st.subheader("Scenario evidence"); st.dataframe(result.traces,hide_index=True,width="stretch"); st.subheader("Measured consequences"); st.json(result.metrics); check=mission.evaluate(result); st.dataframe([{"Requirement":r.label,"Actual":r.actual,"Expected":r.expected,"Passed":"Yes" if r.passed else "No"} for r in check.requirements],hide_index=True,width="stretch")
    explanations={}
    for prompt in mission.reflection_prompts:
        key=f"{mission_id}.{prompt.id}"; answer=st.text_area(prompt.label,value=st.session_state["responses"].get(key,""),help=prompt.help or None,key="reflection."+key,height=130); set_response(st,key,answer); explanations[prompt.id]=answer; st.caption(f"{len(answer.split())} words; minimum 40")
    ready=all(len(v.split())>=40 for v in explanations.values())
    if check.passed: st.success(check.summary)
    else: st.warning("This configuration fails one or more explicit requirements. Use the row-level evidence to revise it.")
    if check.passed and ready and st.session_state["checked_run_ids"].get(mission_id)!=result.run_id:
        if st.button("Check and save this exact design",type="primary"): mark_checked(st,result); save_mission(result,check,explanations); st.rerun()
    elif not ready: st.info("Complete every explanation with at least 40 words before saving.")
    if st.session_state["checked_run_ids"].get(mission_id)==result.run_id:
        st.success("This exact configuration, evidence table, metrics, and analysis are saved."); last=mission_id==LAB.missions[-1]
        if st.button("Continue to final submission" if last else "Continue to next mission",type="primary"): mark_complete(st,mission_id); set_stage(st,"final_submission") if last else st.rerun()

