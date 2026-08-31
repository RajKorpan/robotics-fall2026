from lab.evidence import load_json
from lab.navigation import set_stage
from lab.session import complete
from lab.submissions import save_mission
from lab.ui import render_checks,response,responses_ready
from evaluation.contracts import redesign_requirements
from evaluation.metrics import matched_comparison

KEYS=("mission_3.rationale","mission_3.comparison","mission_3.next_iteration")
def render(st):
    st.header("Mission 3 — Redesign and matched retest")
    st.write("Implement at least two changes tied to baseline evidence. Examples include an earlier intent cue, persistent listening indicator, explicit interpretation/confirmation, longer timeout, visible recovery instructions, cancel/stop affordances, or redundant text and color cues. Do not rely on color alone.")
    st.code("# Copy, edit, and launch your redesign configuration\ncp ros2_ws/src/week11_hri_demo/config/redesign_starter.yaml runtime/redesign.yaml\n./scripts/launch_interaction.sh runtime/redesign.yaml\n\n# Assemble baseline + redesign + design_changes, then evaluate\npython3 scripts/evaluate_trials.py redesign runtime/comparison_raw.json \\\n  --output runtime/comparison_checked.json",language="bash")
    st.warning("Retest the same five scenarios with the same participant code when possible. This improves within-session comparison but introduces learning/order effects; it does not establish general usability.")
    evidence_file=st.file_uploader("comparison_checked.json",type="json",key="m3.evidence"); config=st.file_uploader("Implemented redesign YAML/code",type=["yaml","yml","py","zip"],key="m3.config"); image=st.file_uploader("Redesigned interface screenshot or state diagram",type=["png","jpg","jpeg","pdf"],key="m3.image"); evidence=load_json(evidence_file)
    if evidence: st.json(matched_comparison(evidence.get("baseline",{}),evidence.get("redesign",{})))
    response(st,KEYS[0],"For each implemented change, cite the baseline observation it addresses and explain the intended mechanism.")
    response(st,KEYS[1],"Compare matched baseline and redesign evidence. Discuss improvements, regressions, unchanged measures, and learning/order effects.")
    response(st,KEYS[2],"Propose the next iteration, including one accessibility improvement and one new failure-recovery test.")
    if st.button("Check Mission 3",type="primary"):
        checks=redesign_requirements(evidence or {}); st.session_state["m3.checks"]=checks; ready=all(r.passed for r in checks) and config is not None and image is not None and responses_ready(st,KEYS)
        if ready: complete(st,"mission_3",evidence); save_mission("mission_3",evidence,st.session_state["responses"],(evidence_file,config,image)); st.success("Mission 3 complete.")
        else: st.warning("Meet every matched-comparison check and submit the implemented redesign plus interface evidence.")
    if st.session_state.get("m3.checks"): render_checks(st,st.session_state["m3.checks"])
    if "mission_3" in st.session_state["completed_missions"] and st.button("Continue to final submission"): set_stage(st,"final")

