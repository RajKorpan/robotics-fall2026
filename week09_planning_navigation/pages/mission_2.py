from lab.evidence import load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import reflections_ready, render_requirements, text_response
from missions.mission_2 import REFLECTIONS, evaluate


def render(st):
    st.header("Mission 2 — Execute and evaluate navigation")
    st.write("Run at least five trials from a reset initial pose: open route, narrow route, repeated route, and two trials with an unexpected obstacle introduced after planning. Do not tune between repetitions unless the trial is explicitly labeled as a redesign.")
    st.code("ros2 run week09_nav_tools navigate_probe --ros-args \\\n  -p trial_id:=open_01 -p condition:=open \\\n  -p goal_x:=0.5 -p goal_y:=0.0 \\\n  -p output:=runtime/evidence/navigation_raw.json\n\npython3 scripts/evaluate_evidence.py navigation runtime/evidence/navigation_raw.json \\\n  --output runtime/evidence/navigation_checked.json", language="bash")
    st.info("Record simulator contacts separately when the simulator exposes them. The supplied `collision_events` is conservatively inferred from LiDAR range and is labeled as a proxy in the raw record.")
    upload = st.file_uploader("navigation_checked.json", type="json", key="m2.json"); bag = st.file_uploader("Optional rosbag or compressed trace", type=["zip", "db3", "mcap"], key="m2.bag"); images = st.file_uploader("At least two RViz images, including a recovery/replan or failure", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="m2.images"); evidence = load_json(upload)
    if evidence: st.metric("Success rate", evidence.get("metrics", {}).get("success_rate", "—")); st.dataframe(evidence.get("rows", []), hide_index=True, width="stretch")
    text_response(st, "mission_2.plan_execution", "Why can an executable path still produce a failed or inefficient navigation trial? Use two measured trials.")
    text_response(st, "mission_2.recovery", "Analyze replanning/recovery behavior after the unexpected obstacle. Was the response timely and appropriate?")
    text_response(st, "mission_2.measurement", "Discuss measurement limitations: collision proxy, localization error, timing, path length, and repeatability.")
    if st.button("Check Mission 2", type="primary"):
        requirements = evaluate(evidence); st.session_state["m2.requirements"] = requirements
        ready = all(r.passed for r in requirements) and len(images) >= 2 and reflections_ready(st.session_state["responses"], (f"mission_2.{k}" for k in REFLECTIONS))
        if ready: complete_mission(st, "mission_2", evidence); save_mission("mission_2", evidence, st.session_state["responses"], (upload, bag, *images)); st.success("Mission 2 complete.")
        else: st.warning("Meet every evidence check, upload two images, and complete each response.")
    if st.session_state.get("m2.requirements"): render_requirements(st, st.session_state["m2.requirements"])
    if "mission_2" in st.session_state["completed_missions"] and st.button("Continue to Mission 3"): set_stage(st, "mission_3")
