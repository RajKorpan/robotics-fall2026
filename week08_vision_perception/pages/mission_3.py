from lab.evidence import evidence_id,load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check,text_response
from missions.mission_3 import evaluate
def render(st):
    st.header("Mission 3 — Perception controls behavior");st.write("Trace and test the complete system: camera → detector → `TargetObservation` → behavior → guarded velocity. The robot searches without a reliable target, centers a reliable off-axis target, approaches only when centered, and stops when close or when observations become stale.")
    st.code("# Pure safety/state test\npython3 scripts/evaluate_behavior.py \\\n  --min-confidence 0.60 --stop-area 0.22 --stale-after 0.60 \\\n  --output runtime/evidence/behavior.json\n\n# Explicitly enable behavior only for the simulation trial\nbash scripts/launch_pipeline.sh learned /camera/image_raw true\n\n# Inspect the live ROS connections and commands\nros2 topic echo /perception/target\nros2 topic echo /student_cmd_vel\nros2 topic echo /cmd_vel",language="bash")
    st.warning("Perform motion tests only in simulation. The independent guard bounds speed and stops stale commands, but you must still keep the simulator visible and stop immediately if behavior is unexpected.")
    evidence_file=st.file_uploader("behavior.json",type=["json"],key="m3.json");screens=st.file_uploader("At least two screenshots or GIFs showing the ROS observation and behavior",type=["png","jpg","jpeg","gif"],accept_multiple_files=True,key="m3.screens");evidence=load_json(evidence_file)
    if evidence:st.dataframe(evidence.get("result",{}).get("rows",[]),hide_index=True,width="stretch")
    text_response(st,"mission_3.system_trace","Trace one camera frame through the nodes and topics to the final guarded command. State what each component contributes.");text_response(st,"mission_3.breakdown","Choose lighting, distance, occlusion, orientation, or background. Explain how a perception failure becomes a behavior failure—or is contained.");text_response(st,"mission_3.fallback","Defend the stale, low-confidence, and distractor responses. What additional fallback would you require outside simulation?")
    if st.button("Check Mission 3",type="primary"):
        check=evaluate(evidence,st.session_state["responses"],len(screens));st.session_state["m3.check"]=check
        if check.passed:
            eid=evidence_id("mission_3",evidence);complete_mission(st,"mission_3",eid);st.session_state["evidence"]={**st.session_state["evidence"],"mission_3":evidence};save_mission("mission_3",{"evidence_id":eid,**evidence},st.session_state["responses"],(evidence_file,*screens))
    if st.session_state.get("m3.check"):render_check(st,st.session_state["m3.check"])
    if "mission_3" in st.session_state["completed_missions"] and st.button("Continue to submission"):set_stage(st,"final")
