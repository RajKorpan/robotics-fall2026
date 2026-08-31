from lab.evidence import evidence_id, load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_2 import evaluate
def render(st):
    st.header("Mission 2 — Compare mapping strategies")
    first = st.session_state["evidence"].get("mission_1")
    st.write("Map the same world again for approximately the same duration, but use a meaningfully different route. Examples: perimeter-first versus room-by-room/frontier sweeps; frequent early revisits versus postponing loop closure. Reset the simulator and SLAM state before the second run.")
    text_response(st, "mission_2.strategy_prediction", "Before the second run: name your two strategies and predict which will improve coverage, continuity, and loop closure. Explain why.")
    st.code("# Stop the first launch, relaunch a clean world, and map with strategy 2\n./scripts/launch_mapping.sh\n# Save under a different directory\nmkdir -p runtime/maps/mission2\nros2 run nav2_map_server map_saver_cli -f runtime/maps/mission2/map\npython3 scripts/analyze_map.py --yaml runtime/maps/mission2/map.yaml --strategy room_by_room --duration-min 7 --output runtime/maps/mission2/evidence.json", language="bash")
    evidence_file = st.file_uploader("Strategy 2 evidence.json", type=["json"], key="m2.evidence"); yaml_file = st.file_uploader("Strategy 2 map YAML", type=["yaml", "yml"], key="m2.yaml"); image_file = st.file_uploader("Strategy 2 map image", type=["pgm"], key="m2.image"); screenshot = st.file_uploader("Strategy 2 RViz screenshot", type=["png", "jpg", "jpeg"], key="m2.screen")
    second = load_json(evidence_file)
    if first and second:
        rows = []
        for label, run in (("Strategy 1", first), ("Strategy 2", second)): rows.append({"run": label, "strategy": run.get("strategy"), "quality_score": run.get("quality_score"), **run.get("metrics", {})})
        st.dataframe(rows, hide_index=True, width="stretch")
    text_response(st, "mission_2.comparison", "Compare both maps using at least three metrics and visible map features. Was your prediction supported?")
    text_response(st, "mission_2.loop_closure", "Describe evidence of a loop closure—or explain why you cannot claim one. What change would distinguish loop closure from ordinary map growth?")
    if st.button("Check Mission 2", type="primary"):
        check = evaluate(first, second, st.session_state["responses"]); st.session_state["m2.check"] = check
        complete_files = all(item is not None for item in (yaml_file, image_file, screenshot))
        if check.passed and complete_files:
            eid = evidence_id("mission_2", first, second); complete_mission(st, "mission_2", eid); st.session_state["evidence"] = {**st.session_state["evidence"], "mission_2": second}
            save_mission("mission_2", {"evidence_id": eid, "strategy_1": first, "strategy_2": second}, st.session_state["responses"], (evidence_file, yaml_file, image_file, screenshot))
        elif check.passed: st.warning("Upload the second map YAML, image, and RViz screenshot.")
    if st.session_state.get("m2.check"): render_check(st, st.session_state["m2.check"])
    if "mission_2" in st.session_state["completed_missions"] and st.button("Continue to Mission 3"): set_stage(st, "mission_3")
