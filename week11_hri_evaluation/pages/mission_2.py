from pathlib import Path
from lab.evidence import load_json
from lab.navigation import set_stage
from lab.session import complete
from lab.submissions import save_mission
from lab.ui import render_checks,response,responses_ready
from evaluation.contracts import baseline_requirements
from evaluation.metrics import summarize

KEYS=("mission_2.observations","mission_2.breakdown","mission_2.limits")
def render(st):
    st.header("Mission 2 — Baseline user test")
    st.write("Read the participant script, confirm consent, and run the five scenarios in the supplied order. Do not teach the interface during a task. If intervention is necessary, record it in the non-identifying note. Debrief afterward and reciprocate as participant for your classmate.")
    st.markdown("For every trial record: task success; whether intent and listening state were understood; recovery without facilitator help; 1–5 predictability and feedback ratings; access barrier; safety stop; completion time; and a brief behavior-focused note.")
    template=(Path(__file__).resolve().parents[1]/"assets/protocol/blank_trials.json").read_bytes(); st.download_button("Download blank trial JSON",template,"baseline_trials.json","application/json")
    evidence_file=st.file_uploader("Checked or raw baseline trial JSON",type="json",key="m2.evidence"); evidence=load_json(evidence_file)
    if evidence: st.json(summarize(evidence)); st.dataframe(evidence.get("trials",[]),hide_index=True,width="stretch")
    response(st,KEYS[0],"Report the most important observed behaviors and ratings. Distinguish participant statements, your observations, and your interpretations.")
    response(st,KEYS[1],"Analyze one breakdown in intention, listening, feedback, predictability, recovery, or access. Identify the interface cause rather than blaming the participant.")
    response(st,KEYS[2],"What can and cannot be concluded from one participant and five scripted tasks? Identify learning, facilitator, and order effects.")
    if st.button("Check Mission 2",type="primary"):
        checks=baseline_requirements(evidence or {}); st.session_state["m2.checks"]=checks; ready=all(r.passed for r in checks) and responses_ready(st,KEYS)
        if ready: complete(st,"mission_2",evidence); save_mission("mission_2",evidence,st.session_state["responses"],(evidence_file,)); st.success("Mission 2 complete.")
        else: st.warning("Complete all five valid scenarios, privacy/consent checks, and explanations.")
    if st.session_state.get("m2.checks"): render_checks(st,st.session_state["m2.checks"])
    if "mission_2" in st.session_state["completed_missions"] and st.button("Continue to Mission 3"): set_stage(st,"mission_3")

