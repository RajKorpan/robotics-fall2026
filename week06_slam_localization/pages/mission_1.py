from lab.evidence import evidence_id, load_json
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_1 import evaluate
def render(st):
    st.header("Mission 1 — Build and inspect a map")
    st.markdown("Launch the TurtleBot3 world and asynchronous SLAM, then teleoperate deliberately. In RViz, display `/scan`, `/map`, the robot model, and TF. Before driving, locate unknown, free, and occupied cells. During the run, watch how the map changes when the robot sees a wall from a new angle or returns to its starting area.")
    st.code("# Terminal 1\nexport ROS_DOMAIN_ID=26\nbash scripts/launch_mapping.sh\n\n# Terminal 2\nsource /opt/ros/jazzy/setup.bash\nexport TURTLEBOT3_MODEL=burger\nros2 run turtlebot3_teleop teleop_keyboard\n\n# Terminal 3: add Map, LaserScan, RobotModel, TF, and Odometry displays\nrviz2\n\n# After 6–8 minutes of mapping\nmkdir -p runtime/maps/mission1\nros2 run nav2_map_server map_saver_cli -f runtime/maps/mission1/map\npython3 scripts/analyze_map.py --yaml runtime/maps/mission1/map.yaml --strategy perimeter_then_interior --duration-min 7 --output runtime/maps/mission1/evidence.json", language="bash")
    st.warning("Stop before changing terminals. Avoid rapid rotation: motion blur and sparse overlap can damage scan matching. Do not edit the map image by hand.")
    evidence_file = st.file_uploader("Mission 1 evidence.json", type=["json"], key="m1.evidence"); yaml_file = st.file_uploader("Saved map YAML", type=["yaml", "yml"], key="m1.yaml"); image_file = st.file_uploader("Saved map image", type=["pgm"], key="m1.image"); screenshot = st.file_uploader("RViz screenshot showing map, scan, and robot", type=["png", "jpg", "jpeg"], key="m1.screen")
    evidence = load_json(evidence_file)
    if evidence: st.dataframe([{**evidence.get("metrics", {}), "quality_score": evidence.get("quality_score")}], hide_index=True, width="stretch")
    text_response(st, "mission_1.system_observation", "Describe how `/scan`, odometry, TF, and `/map` changed during your run. Include one concrete observation from RViz.")
    text_response(st, "mission_1.map_interpretation", "Interpret your known fraction, speckle fraction, border contact, and quality score. What looks reliable or questionable?")
    text_response(st, "mission_1.limitations", "Identify one area the robot did not observe well and explain how route or sensor geometry caused the limitation.")
    if st.button("Check Mission 1", type="primary"):
        check = evaluate(evidence, st.session_state["responses"], yaml_file is not None, image_file is not None); st.session_state["m1.check"] = check
        if check.passed and screenshot is not None:
            eid = evidence_id("mission_1", evidence); complete_mission(st, "mission_1", eid); st.session_state["evidence"] = {**st.session_state["evidence"], "mission_1": evidence}
            save_mission("mission_1", {"evidence_id": eid, **evidence}, st.session_state["responses"], (evidence_file, yaml_file, image_file, screenshot))
        elif check.passed: st.warning("Add the required RViz screenshot before completing the mission.")
    if st.session_state.get("m1.check"): render_check(st, st.session_state["m1.check"])
    if "mission_1" in st.session_state["completed_missions"] and st.button("Continue to Mission 2"): set_stage(st, "mission_2")
