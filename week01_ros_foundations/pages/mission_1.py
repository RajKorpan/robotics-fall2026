from __future__ import annotations

from lab.evidence import evidence_id, latest_graph
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import choice_response, render_check, text_response
from missions.mission_1 import REQUIRED_TOPICS, evaluate


ROLES = ["Sensing", "Decision/control", "Actuation", "Simulation", "Visualization", "Infrastructure"]
PIPELINE_ROLES = ["Sense", "Decide", "Act", "Support"]


def render(st) -> None:
    st.title("Mission 1: Observe the robot")
    st.write("Determine how the simulated robot is organized and how information moves through it.")
    st.code("bash scripts/launch_lab.sh", language="bash")

    graph = latest_graph()
    if not graph:
        st.warning("No ROS graph snapshot is available. Launch the lab system, then refresh.")
        if st.button("Refresh graph"):
            st.rerun()
        return

    nodes = [str(item.get("name", item)) for item in graph.get("nodes", [])]
    topics = graph.get("topics", [])
    services = graph.get("services", [])
    st.success(
        f"Evidence collector sees {len(nodes)} nodes, {len(topics)} topics, "
        f"and {len(services)} services."
    )

    with st.expander("Inspection commands", expanded=True):
        st.code(
            "ros2 node list\n"
            "ros2 node info /NODE_NAME\n"
            "ros2 topic list -t\n"
            "ros2 topic info /scan --verbose\n"
            "ros2 interface show sensor_msgs/msg/LaserScan\n"
            "ros2 topic echo /scan --once\n"
            "ros2 topic echo /odom --once\n"
            "ros2 service list -t",
            language="bash",
        )

    st.subheader("Classify the nodes as a system")
    st.caption(
        "Classify at least five twice: first by subsystem responsibility, then by its "
        "primary place in the sense–decide–act loop. Use Support for simulation, visualization, or infrastructure."
    )
    roles = dict(response(st, "mission_1.node_roles", {}))
    pipeline_roles = dict(response(st, "mission_1.pipeline_roles", {}))
    for name in nodes[:12]:
        values = ["Not classified", *ROLES]
        prior = roles.get(name, "Not classified")
        pipeline_values = ["Not classified", *PIPELINE_ROLES]
        pipeline_prior = pipeline_roles.get(name, "Not classified")
        col1, col2 = st.columns(2)
        with col1:
            roles[name] = st.selectbox(
                f"{name} — subsystem",
                values,
                index=values.index(prior) if prior in values else 0,
                key=f"role.{name}",
            )
        with col2:
            pipeline_roles[name] = st.selectbox(
                f"{name} — pipeline",
                pipeline_values,
                index=pipeline_values.index(pipeline_prior) if pipeline_prior in pipeline_values else 0,
                key=f"pipeline_role.{name}",
            )
    set_response(st, "mission_1.node_roles", {key: value for key, value in roles.items() if value != "Not classified"})
    set_response(st, "mission_1.pipeline_roles", {key: value for key, value in pipeline_roles.items() if value != "Not classified"})

    st.subheader("Identify message types")
    type_options = [
        "Select a type",
        "sensor_msgs/msg/LaserScan",
        "nav_msgs/msg/Odometry",
        "geometry_msgs/msg/Twist",
        "sensor_msgs/msg/JointState",
        "tf2_msgs/msg/TFMessage",
    ]
    topic_types = dict(response(st, "mission_1.topic_types", {}))
    columns = st.columns(3)
    for column, topic in zip(columns, REQUIRED_TOPICS):
        prior = topic_types.get(topic, type_options[0])
        with column:
            selected = st.selectbox(topic, type_options, index=type_options.index(prior) if prior in type_options else 0, key=f"type.{topic}")
            topic_types[topic] = "" if selected == type_options[0] else selected
    set_response(st, "mission_1.topic_types", topic_types)

    st.subheader("Connect the system")
    connections = dict(response(st, "mission_1.connections", {}))
    questions = (
        ("teleop_output", "Teleoperation publishes commands on", ["/scan", "/odom", "/student_cmd_vel", "/cmd_vel"]),
        ("guard_input", "The command guard subscribes to", ["/scan", "/student_cmd_vel", "/cmd_vel", "/tf"]),
        ("guard_output", "The command guard publishes guarded commands on", ["/scan", "/student_cmd_vel", "/cmd_vel", "/odom"]),
        ("lidar_output", "The LiDAR/simulator publishes measurements on", ["/scan", "/odom", "/cmd_vel", "/joint_states"]),
        ("odometry_output", "The robot controller publishes pose estimates on", ["/scan", "/odom", "/cmd_vel", "/tf_static"]),
    )
    for key, label, options in questions:
        values = ["Select", *options]
        prior = connections.get(key, values[0])
        selected = st.selectbox(label, values, index=values.index(prior) if prior in values else 0, key=f"connection.{key}")
        connections[key] = "" if selected == values[0] else selected
    set_response(st, "mission_1.connections", connections)

    st.subheader("Inspect request/response communication")
    st.write(
        "Topics carry ongoing streams. Services represent a request followed by a response. "
        "Inspect, but do not call, an unfamiliar service."
    )
    if services:
        st.dataframe(services[:20], hide_index=True, width="stretch")
    service_example = dict(response(st, "mission_1.service_example", {}))
    service_example["name"] = st.text_input(
        "One observed service name",
        value=str(service_example.get("name", "")),
        key="service_example.name",
    )
    service_example["type"] = st.text_input(
        "Its service type",
        value=str(service_example.get("type", "")),
        key="service_example.type",
    )
    service_example["purpose"] = st.text_area(
        "Based on its name and type, what request/response purpose does it likely serve?",
        value=str(service_example.get("purpose", "")),
        key="service_example.purpose",
    )
    set_response(st, "mission_1.service_example", service_example)

    st.subheader("Explain what you observed")
    text_response(st, "mission_1.node_vs_topic", "What is the difference between a node and a topic?")
    text_response(st, "mission_1.sense_decide_act", "Which observed components sense, decide, and act?")
    text_response(st, "mission_1.multiple_subscribers", "Why can multiple nodes receive /scan without consuming it?")
    text_response(st, "mission_1.teleop_change", "What changes in the ROS graph when teleoperation starts?")
    text_response(st, "mission_1.rviz_role", "Is RViz part of control or an observer? Defend your answer.")
    text_response(st, "mission_1.service_vs_topic", "Use your live evidence to explain how a service differs from a topic.")
    text_response(st, "mission_1.middleware_evidence", "What live evidence supports describing ROS 2 as middleware rather than as the robot's operating system?")
    text_response(st, "mission_1.failure_diagnosis", "Choose one missing node, topic, or message connection and predict the observable failure it would cause.")
    text_response(st, "mission_1.architecture_observation", "Is the system you observed purely reactive, behavior-based, deliberative, or hybrid? State what is actually present and avoid claiming a planner that you did not observe.")

    check = evaluate(graph, st.session_state.get("responses", {}))
    render_check(st, check)
    current_id = evidence_id(
        graph,
        response(st, "mission_1.node_roles", {}),
        response(st, "mission_1.pipeline_roles", {}),
        response(st, "mission_1.connections", {}),
        response(st, "mission_1.service_example", {}),
    )
    checked_id = st.session_state.get("checked_evidence_ids", {}).get("mission_1")
    if check.passed and checked_id != current_id:
        if st.button("Check and save Mission 1", type="primary"):
            evidence = {"evidence_id": current_id, "graph": graph, "check": [item.__dict__ for item in check.requirements]}
            save_mission("mission_1", evidence, st.session_state.get("responses", {}))
            complete_mission(st, "mission_1", current_id)
            st.rerun()
    if checked_id == current_id:
        st.success("This graph investigation is saved.")
        if st.button("Continue to Mission 2", type="primary"):
            set_stage(st, "mission_2")
