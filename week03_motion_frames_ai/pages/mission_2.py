from __future__ import annotations

from lab.evidence import evidence_id, frame_snapshot
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_2 import DIAGNOSTICS, RELATIONSHIPS, evaluate


def render(st) -> None:
    st.title("Mission 2: Frames and transformations")
    st.write("A coordinate is meaningful only together with the frame in which it is expressed.")
    st.code(
        "ros2 run tf2_tools view_frames\n"
        "ros2 run tf2_ros tf2_echo odom base_link\n"
        "ros2 run tf2_ros tf2_echo base_link base_scan\n"
        "ros2 run course_motion_tools frame_probe",
        language="bash",
    )
    snapshot = frame_snapshot()
    if not snapshot:
        st.warning("No frame snapshot found. Run frame_probe, then refresh.")
        if st.button("Refresh frames"):
            st.rerun()
        return
    st.subheader("Observed frame tree")
    st.code(" → ".join(snapshot.get("frame_chain", [])))
    st.json(snapshot.get("transforms", {}), expanded=False)

    relationships = dict(response(st, "mission_2.relationships", {}))
    options = ["Select", *RELATIONSHIPS.values(), "Sensor frame fixed to the world", "Odometry frame fixed to the sensor"]
    for key, label in (
        ("odom_to_base", "Which relationship tracks robot motion?"),
        ("base_to_sensor", "Which relationship represents the sensor mounting?"),
        ("map_role", "What is the purpose of the map frame when localization is active?"),
    ):
        prior = relationships.get(key, "Select")
        value = st.selectbox(label, options, index=options.index(prior) if prior in options else 0, key=f"relationship.{key}")
        relationships[key] = "" if value == "Select" else value
    set_response(st, "mission_2.relationships", relationships)

    st.subheader("Transform two points")
    st.write("Use the observed transforms or tf2 tools. Enter values to two decimal places.")
    point_answers = dict(response(st, "mission_2.point_answers", {}))
    for key, prompt in snapshot.get("point_prompts", {}).items():
        st.code(prompt)
        prior = point_answers.get(key, {})
        col1, col2 = st.columns(2)
        with col1:
            x = st.number_input("x", value=float(prior.get("x", 0.0)), step=0.01, key=f"point.{key}.x")
        with col2:
            y = st.number_input("y", value=float(prior.get("y", 0.0)), step=0.01, key=f"point.{key}.y")
        point_answers[key] = {"x": x, "y": y}
    set_response(st, "mission_2.point_answers", point_answers)

    st.subheader("Diagnose frame failures")
    diagnostics = dict(response(st, "mission_2.diagnostics", {}))
    diagnostic_options = ["Select", *DIAGNOSTICS.values(), "Velocity limit exceeded"]
    prompts = {
        "typo": "A message uses frame_id='base_lnik'.",
        "wrong_source": "A LiDAR point is labeled as odom even though its coordinates are sensor-relative.",
        "stale": "A transform is requested for a timestamp outside the TF buffer.",
    }
    for key, prompt in prompts.items():
        prior = diagnostics.get(key, "Select")
        value = st.selectbox(prompt, diagnostic_options, index=diagnostic_options.index(prior) if prior in diagnostic_options else 0, key=f"diagnostic.{key}")
        diagnostics[key] = "" if value == "Select" else value
    set_response(st, "mission_2.diagnostics", diagnostics)

    text_response(st, "mission_2.fixed_meaning", "What does each of odom, base_link, and base_scan remain fixed to?")
    text_response(st, "mission_2.moving_coordinates", "Which coordinates change when the robot moves, and in which frame?")
    text_response(st, "mission_2.sensor_offset", "Why must software know the sensor's mounting transform?")
    text_response(st, "mission_2.map_absent", "Why might no map frame exist in this lab yet?")
    check = evaluate(snapshot, st.session_state.get("responses", {}))
    render_check(st, check)
    current_id = evidence_id(snapshot, relationships, point_answers, diagnostics)
    checked = st.session_state.get("checked_evidence_ids", {}).get("mission_2")
    if check.passed and checked != current_id and st.button("Check and save Mission 2", type="primary"):
        save_mission("mission_2", {"evidence_id": current_id, "snapshot": snapshot, "check": [item.__dict__ for item in check.requirements]}, st.session_state.get("responses", {}))
        complete_mission(st, "mission_2", current_id)
        st.rerun()
    if checked == current_id:
        st.success("This frame analysis is saved.")
        if st.button("Continue to Mission 3", type="primary"):
            set_stage(st, "mission_3")

