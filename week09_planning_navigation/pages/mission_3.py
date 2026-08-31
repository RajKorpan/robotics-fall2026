from lab.evidence import load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import reflections_ready, render_requirements, text_response
from missions.mission_3 import REFLECTIONS, evaluate


def render(st):
    st.header("Mission 3 — Human-aware navigation challenge")
    st.write("Use `seated_person_corridor`. First preserve the baseline: the route should be collision-free yet violate the scenario's 0.75 m person-clearance rule. Then make at least two concrete changes—such as a keepout region, inflation/personal-space layer, speed region, or controller limit—and repeat the identical start and goal.")
    st.code("# Terminal A; Ctrl-C after each navigation run to save the trace\nros2 run week09_nav_tools social_monitor --ros-args \\\n  -p scenario_file:=assets/scenarios/people.json \\\n  -p run_label:=baseline -p goal_id:=social_goal \\\n  -p output:=runtime/evidence/baseline_social.json\n\n# Merge config/human_aware_costmap_fragment.yaml into your full Nav2 params.\n# Supply keepout/speed masks through map_server + CostmapFilterInfoServer.\n# Repeat with run_label:=redesign, then assemble human_aware_raw.json.\npython3 scripts/evaluate_evidence.py human-aware runtime/evidence/human_aware_raw.json \\\n  --output runtime/evidence/human_aware_checked.json", language="bash")
    st.caption("The policy values are deliberately scenario-specific. Your analysis should discuss how context, culture, disability, robot size, urgency, and consent could require different values.")
    upload = st.file_uploader("human_aware_checked.json", type="json", key="m3.json"); config = st.file_uploader("Merged Nav2 YAML or mask archive", type=["yaml", "yml", "zip", "pgm", "png"], key="m3.config"); images = st.file_uploader("Matched baseline and redesign RViz images", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="m3.images"); evidence = load_json(upload)
    if evidence:
        st.json({"policy": evidence.get("policy"), "baseline": evidence.get("baseline", {}).get("metrics"), "redesign": evidence.get("redesign", {}).get("metrics"), "changes": evidence.get("parameter_changes")})
    text_response(st, "mission_3.appropriateness", "Why was the baseline technically successful but socially inappropriate in this scenario? Use measured clearance and speed.")
    text_response(st, "mission_3.redesign", "Explain each configuration/costmap/rule change and the causal mechanism by which it changed behavior.")
    text_response(st, "mission_3.tradeoff", "Evaluate the redesign's safety, time/path-length trade-offs and limits. When should policy or human confirmation override shortest path?")
    if st.button("Check Mission 3", type="primary"):
        requirements = evaluate(evidence); st.session_state["m3.requirements"] = requirements
        ready = all(r.passed for r in requirements) and config is not None and len(images) >= 2 and reflections_ready(st.session_state["responses"], (f"mission_3.{k}" for k in REFLECTIONS))
        if ready: complete_mission(st, "mission_3", evidence); save_mission("mission_3", evidence, st.session_state["responses"], (upload, config, *images)); st.success("Mission 3 complete.")
        else: st.warning("Meet every check and submit matched images, actual configuration, and explanations.")
    if st.session_state.get("m3.requirements"): render_requirements(st, st.session_state["m3.requirements"])
    if "mission_3" in st.session_state["completed_missions"] and st.button("Continue to final submission"): set_stage(st, "final")
