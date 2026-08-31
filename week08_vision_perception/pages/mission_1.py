from lab.evidence import evidence_id,load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check,text_response
from missions.mission_1 import evaluate
def render(st):
    st.header("Mission 1 — Classical perception");st.write("Detect the green course target with HSV thresholding, morphology, contour filtering, and a minimum-area rule. Tune on normal images first, lock your parameters, then evaluate all eight conditions without condition-specific retuning.")
    st.code("python3 scripts/generate_condition_bank.py\n./scripts/launch_pipeline.sh classical /camera/image_raw\n\n# Publish one condition in another terminal\nros2 run image_publisher image_publisher_node runtime/condition_bank/normal.png --ros-args -r image_raw:=/camera/image_raw\n\n# Record that condition; repeat with the matching expected value\nros2 run week08_perception observation_recorder --ros-args \\\n  -p condition:=normal -p expected:=true -p duration:=5.0 \\\n  -p output:=runtime/evidence/classical.csv\n\npython3 scripts/evaluate_perception.py --csv runtime/evidence/classical.csv \\\n  --method classical --output runtime/evidence/classical.json",language="bash")
    st.caption("Use `ros2 param set /classical_detector ...` to tune hue, saturation, value, morphology kernel, and minimum area. Capture both `/perception/mask` and `/perception/annotated` with `image_view` or RViz.")
    evidence_file=st.file_uploader("classical.json",type=["json"],key="m1.json");raw=st.file_uploader("classical.csv",type=["csv"],key="m1.csv");images=st.file_uploader("At least four masks/annotations, including a failure",type=["png","jpg","jpeg"],accept_multiple_files=True,key="m1.images");evidence=load_json(evidence_file)
    if evidence:st.dataframe([evidence.get("metrics",{})],hide_index=True,width="stretch");st.dataframe(evidence.get("rows",[]),hide_index=True,width="stretch")
    text_response(st,"mission_1.prediction","Compare your original prediction with the observed condition results. Identify at least one surprise.");text_response(st,"mission_1.parameter_effect","Explain how HSV bounds, morphology, and minimum contour area changed precision and recall.");text_response(st,"mission_1.failure_analysis","Analyze one false positive or false negative. What image evidence caused the rule-based pipeline to fail?")
    if st.button("Check Mission 1",type="primary"):
        check=evaluate(evidence,st.session_state["responses"],len(images));st.session_state["m1.check"]=check
        if check.passed and raw:
            eid=evidence_id("mission_1",evidence);complete_mission(st,"mission_1",eid);st.session_state["evidence"]={**st.session_state["evidence"],"mission_1":evidence};save_mission("mission_1",{"evidence_id":eid,**evidence},st.session_state["responses"],(evidence_file,raw,*images))
        elif check.passed:st.warning("Upload the raw CSV before completing the mission.")
    if st.session_state.get("m1.check"):render_check(st,st.session_state["m1.check"])
    if "mission_1" in st.session_state["completed_missions"] and st.button("Continue to Mission 2"):set_stage(st,"mission_2")
