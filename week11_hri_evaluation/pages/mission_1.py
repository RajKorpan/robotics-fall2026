from lab.evidence import load_json
from lab.navigation import set_stage
from lab.session import complete
from lab.submissions import save_mission
from lab.ui import render_checks,response,responses_ready
from evaluation.contracts import prototype_requirements

KEYS=("mission_1.flow","mission_1.predictions","mission_1.safety")
def render(st):
    st.header("Mission 1 — Understand and dry-run the prototype")
    st.write("Run the baseline twice without a participant. Exercise the success, ambiguity, timeout, correction, cancellation, and emergency-stop paths. Observe both `/hri/state` and `/hri/display`; verify no peer-test command reaches `/cmd_vel`.")
    st.code("ros2 run week11_hri_demo event_recorder --ros-args \\\n+  -p trial_id:=dry_run_01 -p design_version:=baseline \\\n+  -p output:=runtime/evidence/dry_run_01.json\n# Ctrl-C after the run so the recorder writes the event trace",language="bash")
    st.markdown("Create `prototype_evidence.json` with `observed_states`, `motion_enabled`, `stop_tested`, and `dry_runs`. Upload the two raw event traces as supporting evidence.")
    evidence_file=st.file_uploader("prototype_evidence.json",type="json",key="m1.evidence"); traces=st.file_uploader("Two dry-run event JSON files",type="json",accept_multiple_files=True,key="m1.traces"); image=st.file_uploader("State diagram or interface screenshot",type=["png","jpg","jpeg","pdf"],key="m1.image"); evidence=load_json(evidence_file)
    response(st,KEYS[0],"Trace a successful interaction from intention cue through completion. Identify what the person can observe at each transition.")
    response(st,KEYS[1],"Before peer testing, predict two points of confusion and state what observation would support or contradict each prediction.")
    response(st,KEYS[2],"Explain the stop, timeout, cancellation, and ambiguity behavior. Which unsafe action does each prevent?")
    if st.button("Check Mission 1",type="primary"):
        checks=prototype_requirements(evidence or {}); st.session_state["m1.checks"]=checks; ready=all(r.passed for r in checks) and len(traces)>=2 and image is not None and responses_ready(st,KEYS)
        if ready: complete(st,"mission_1",evidence); save_mission("mission_1",evidence,st.session_state["responses"],(evidence_file,*traces,image)); st.success("Mission 1 complete.")
        else: st.warning("Meet every check, include two traces and a diagram/image, and complete each explanation.")
    if st.session_state.get("m1.checks"): render_checks(st,st.session_state["m1.checks"])
    if "mission_1" in st.session_state["completed_missions"] and st.button("Continue to Mission 2"): set_stage(st,"mission_2")

