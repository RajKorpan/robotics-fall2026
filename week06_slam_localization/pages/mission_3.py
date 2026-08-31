from lab.evidence import evidence_id, load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_3 import CONDITIONS, evaluate

LABELS = {"good_initial_pose": "Good initial pose", "incorrect_initial_pose": "Incorrect initial pose", "ambiguous_location": "Ambiguous location", "degraded_sensor": "Degraded scan"}

def render(st):
    st.header("Mission 3 — Localize in the saved map")
    st.write("Use the better of your two saved maps. Restart the simulator and localization for each condition so history does not leak between trials. Keep the robot still while setting the initial pose, then drive slowly enough for scan matching.")
    st.code("# Normal trials: replace the path with your absolute YAML path\nbash scripts/launch_localization.sh /absolute/path/to/map.yaml normal\n\n# In another sourced terminal, after setting the initial pose in RViz\nros2 run course_slam_tools localization_recorder --ros-args \\\n  -p condition:=good_initial_pose -p duration:=30.0 \\\n  -p output:=runtime/evidence/good_initial_pose.json", language="bash")
    st.markdown("""
**Good initial pose:** place the estimate close to the simulated robot with a matching heading.  
**Incorrect initial pose:** place it at least 1 m away or rotate it at least 90°, then move through distinctive geometry and observe recovery.  
**Ambiguous location:** initialize in a visually similar corridor or symmetric area. Watch the particle cloud, covariance, and competing hypotheses.  
**Degraded scan:** restart with `bash scripts/launch_localization.sh /absolute/path/to/map.yaml degraded`, which routes AMCL through the supplied 50%-retention noisy scan proxy. Use `condition:=degraded_sensor` in the recorder command.
""")
    trials = {}
    uploads = []
    columns = st.columns(2)
    for index, condition in enumerate(CONDITIONS):
        with columns[index % 2]:
            upload = st.file_uploader(f"{LABELS[condition]} JSON", type=["json"], key=f"m3.{condition}"); uploads.append(upload)
            evidence = load_json(upload)
            if evidence and evidence.get("condition") == condition:
                trials[condition] = evidence; st.dataframe([evidence.get("metrics", {})], hide_index=True, width="stretch")
            elif evidence: st.error(f"Expected condition `{condition}` in this file.")
    screenshots = st.file_uploader("RViz screenshots showing the particle cloud or pose estimate (at least two conditions)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    text_response(st, "mission_3.knowing_where", "What evidence would justify saying the robot knows where it is? Use pose, covariance/particle spread, scan agreement, and behavior in your answer.")
    text_response(st, "mission_3.recovery", "Compare the good and incorrect initial-pose trials. How did recovery appear in the metrics and RViz, and what action helped or hindered it?")
    text_response(st, "mission_3.sensor_effect", "Compare normal and degraded sensing. Explain the observed change without claiming that covariance is guaranteed to equal true error.")
    text_response(st, "mission_3.deployment_limit", "Describe one dangerous false-confidence case, a detection or fallback mechanism, and who could be affected if localization is wrong.")
    if st.button("Check Mission 3", type="primary"):
        check = evaluate(trials, st.session_state["responses"]); st.session_state["m3.check"] = check
        if check.passed and len(screenshots) >= 2:
            eid = evidence_id("mission_3", trials); complete_mission(st, "mission_3", eid); st.session_state["evidence"] = {**st.session_state["evidence"], "mission_3": trials}
            save_mission("mission_3", {"evidence_id": eid, "trials": trials}, st.session_state["responses"], tuple(uploads) + tuple(screenshots))
        elif check.passed: st.warning("Upload screenshots from at least two localization conditions.")
    if st.session_state.get("m3.check"): render_check(st, st.session_state["m3.check"])
    if "mission_3" in st.session_state["completed_missions"] and st.button("Continue to submission"): set_stage(st, "final")
