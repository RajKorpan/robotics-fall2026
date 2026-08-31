from lab.evidence import load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import reflections_ready, render_requirements, text_response
from missions.mission_1 import REFLECTIONS, evaluate


def render(st):
    st.header("Mission 1 — Predict and inspect plans")
    st.write("Before sending any goal, sketch the route and predict reachability, length, and tightest clearance. Then run all five standard goals with Nav2's `ComputePathToPose` action. A rejected impossible goal is useful evidence, not a broken experiment.")
    st.code("# Repeat with poses/labels from assets/scenarios/goals.json\nros2 run week09_nav_tools plan_probe --ros-args \\\n  -p goal_id:=open_short -p goal_x:=0.5 -p goal_y:=0.0 \\\n  -p expected_reachable:=true -p output:=runtime/evidence/plans_raw.json\n\npython3 scripts/evaluate_evidence.py plans runtime/evidence/plans_raw.json \\\n  --output runtime/evidence/plans_checked.json", language="bash")
    st.warning("The recorder leaves `minimum_clearance_m` null. Measure it in RViz against the inflated costmap or calculate it from an exported costmap; document your method and fill the field before evaluation.")
    upload = st.file_uploader("plans_checked.json", type="json", key="m1.json"); images = st.file_uploader("Three RViz path images (short, detour/narrow, rejected goal)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="m1.images"); evidence = load_json(upload)
    if evidence: st.dataframe(evidence.get("rows", []), hide_index=True, width="stretch")
    text_response(st, "mission_1.prediction", "Compare predicted and observed path shapes, lengths, and clearance. Where was your mental model wrong?")
    text_response(st, "mission_1.comparison", "Compare the short, detour, and narrow paths. Explain how costmap inflation and obstacles affected them.")
    text_response(st, "mission_1.failure", "For each impossible goal, explain the failure evidence and how you ruled out slow planning or a disconnected action server.")
    if st.button("Check Mission 1", type="primary"):
        requirements = evaluate(evidence); st.session_state["m1.requirements"] = requirements
        ready = all(r.passed for r in requirements) and len(images) >= 3 and reflections_ready(st.session_state["responses"], (f"mission_1.{k}" for k in REFLECTIONS))
        if ready: complete_mission(st, "mission_1", evidence); save_mission("mission_1", evidence, st.session_state["responses"], (upload, *images)); st.success("Mission 1 complete.")
        else: st.warning("Meet every evidence check, upload three images, and write at least 35 words per response.")
    if st.session_state.get("m1.requirements"): render_requirements(st, st.session_state["m1.requirements"])
    if "mission_1" in st.session_state["completed_missions"] and st.button("Continue to Mission 2"): set_stage(st, "mission_2")

