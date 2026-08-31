from lab.evidence import evidence_id,load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check,text_response
from missions.mission_2 import evaluate
def render(st):
    st.header("Mission 2 — Learned perception");st.write("Run the frozen pretrained detector on the robot camera or supplied recorded run. Use a supported target class chosen by the instructor. Do not train or replace the model. Record the same environmental dimensions and sweep the confidence threshold after data collection.")
    st.code("bash scripts/launch_pipeline.sh learned /camera/image_raw\n# Set the assigned target class and initial threshold\nros2 param set /learned_detector target_label bottle\nros2 param set /learned_detector confidence_threshold 0.20\n# Record every condition to learned.csv, then evaluate\npython3 scripts/evaluate_perception.py --csv runtime/evidence/learned.csv \\\n  --method learned --selected-threshold 0.50 \\\n  --output runtime/evidence/learned.json",language="bash")
    st.info("Collect detections once at a permissive threshold, then apply the threshold sweep offline. This keeps the underlying observations fixed and makes the comparison controlled.")
    evidence_file=st.file_uploader("learned.json",type=["json"],key="m2.json");raw=st.file_uploader("learned.csv",type=["csv"],key="m2.csv");images=st.file_uploader("At least four annotated learned detections, including false or missed cases",type=["png","jpg","jpeg"],accept_multiple_files=True,key="m2.images");evidence=load_json(evidence_file)
    if evidence:
        st.dataframe(evidence.get("threshold_sweep",[]),hide_index=True,width="stretch");st.dataframe(evidence.get("rows",[]),hide_index=True,width="stretch")
    text_response(st,"mission_2.threshold_tradeoff","Use the sweep to justify your selected operating threshold. Discuss both false positives and false negatives.");text_response(st,"mission_2.comparison","Compare the classical and learned systems under at least three conditions. When is each preferable?");text_response(st,"mission_2.confidence_limit","Analyze one confident error or uncertain correct detection. Why is detector confidence not a safety guarantee?")
    if st.button("Check Mission 2",type="primary"):
        check=evaluate(evidence,st.session_state["responses"],len(images));st.session_state["m2.check"]=check
        if check.passed and raw:
            eid=evidence_id("mission_2",evidence);complete_mission(st,"mission_2",eid);st.session_state["evidence"]={**st.session_state["evidence"],"mission_2":evidence};save_mission("mission_2",{"evidence_id":eid,**evidence},st.session_state["responses"],(evidence_file,raw,*images))
        elif check.passed:st.warning("Upload the raw CSV before completing the mission.")
    if st.session_state.get("m2.check"):render_check(st,st.session_state["m2.check"])
    if "mission_2" in st.session_state["completed_missions"] and st.button("Continue to Mission 3"):set_stage(st,"mission_3")
