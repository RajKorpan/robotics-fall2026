from __future__ import annotations

from lab.evidence import evidence_id, latest_graph
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_1 import GUIDED_CHECKS, evaluate, mission_responses, stable_graph


CHECK_LABELS = {
    "node_list": "Run `ros2 node list` and find the four highlighted nodes",
    "guard_info": "Inspect the command guard and find its input and output topics",
    "bridge_info": "Inspect the simulator bridge and find `/scan`, `/odom`, and `/cmd_vel`",
    "scan_info": "Inspect who publishes and subscribes to `/scan`",
    "scan_message": "Display one `/scan` message and find its `ranges` field",
    "command_topics": "Compare `/student_cmd_vel` with `/cmd_vel`",
}

TOPIC_MEANINGS = {
    "/scan": "LiDAR distance measurements around the robot",
    "/odom": "The robot's running estimate of its position, direction, and movement",
    "/student_cmd_vel": "A proposed driving command from a student program or tool",
    "/cmd_vel": "The final driving command sent toward the robot after the safety check",
    "/tf": "Relationships between robot coordinate frames, such as the body and sensors",
}


def _topic_map(graph: dict) -> dict[str, dict]:
    return {
        str(item.get("name", "")): item
        for item in graph.get("topics", [])
        if isinstance(item, dict) and item.get("name")
    }


def _mark_observation(st, checks: dict, key: str, label: str) -> None:
    checks[key] = st.checkbox(label, value=bool(checks.get(key)), key=f"mission1.check.{key}")


def render(st) -> None:
    st.title("Mission 1: Meet the ROS 2 robot system")
    st.write(
        "This mission moves from the small examples in Part 3 to a real simulated robot. "
        "You will be told what each tool and component does before you inspect it."
    )

    st.subheader("Before you begin: what will open?")
    left, middle, right = st.columns(3)
    with left:
        st.markdown(
            "**Gazebo**\n\nA robot simulator. It calculates the virtual world's physics, including motion, "
            "walls, wheels, and sensor readings."
        )
    with middle:
        st.markdown(
            "**TurtleBot3 World**\n\nThe practice environment inside Gazebo. TurtleBot3 Burger is the small mobile "
            "robot placed in that environment."
        )
    with right:
        st.markdown(
            "**RViz**\n\nA data viewer for ROS 2. It displays information such as sensor readings and robot "
            "position. It does not simulate the physics."
        )

    st.subheader("What is a ROS 2 graph?")
    st.write(
        "A ROS 2 graph is a live map of the software components that are running and the ways they "
        "communicate. A node is one running program. A topic is a named channel that carries a stream "
        "of messages. A publisher sends messages to a topic. A subscriber receives them."
    )
    st.info("publisher node  →  topic carrying messages  →  subscriber node")
    st.write(
        "For example, the simulator bridge publishes distance readings on `/scan`. The evidence "
        "collector subscribes to `/scan` so it can record those readings for this guide."
    )
    st.info("`/ros_gz_bridge`  →  `/scan`  →  `/course_evidence_collector`")

    st.subheader("Step 1: Launch the simulated robot")
    st.markdown(
        "1. In the browser desktop terminal, run the command below and keep it running.\n"
        "2. Wait for Gazebo and RViz to open.\n"
        "3. In Gazebo, locate the small wheeled TurtleBot3.\n"
        "4. Confirm that RViz opens. It may initially show only a grid and display panels. You do not need to configure it.\n"
        "5. Return here and click **Refresh live graph**."
    )
    st.code("bash scripts/launch_lab.sh", language="bash")
    if st.button("Refresh live graph", type="primary"):
        st.rerun()

    graph = latest_graph()
    if not graph:
        st.warning("The guide cannot see the robot system yet. Finish the five launch steps above, then refresh.")
        return

    nodes = {str(item.get("name", item)) for item in graph.get("nodes", [])}
    topics = _topic_map(graph)
    st.success(f"The live ROS 2 graph is available. It currently contains {len(nodes)} nodes and {len(topics)} topics.")

    with st.expander("Terminal setup and recovery"):
        st.write(
            "Open another terminal in the browser desktop for the inspection commands. New terminals "
            "should load ROS 2 automatically. If `ros2` is not found, run the recovery commands first."
        )
        st.code(
            "source /opt/ros/jazzy/setup.bash\n"
            "source /workspace/week01_ros_foundations/ros2_ws/install/setup.bash\n"
            "export ROS_DOMAIN_ID=24",
            language="bash",
        )

    checks = dict(response(st, "mission_1.guided_checks", {}))

    st.subheader("Step 2: Take a guided tour of four nodes")
    st.write(
        "You do not need to guess what unfamiliar node names mean. The four important nodes are "
        "introduced below. Run the listed commands only to confirm the highlighted connections."
    )
    st.markdown(
        "- **`/ros_gz_bridge`** translates between Gazebo and ROS 2. It carries sensor information "
        "out of the simulator and driving commands into it. It contributes to both sensing and acting.\n"
        "- **`/course_cmd_vel_guard`** receives a proposed driving command and publishes the command "
        "that is allowed to reach the robot. It performs a small safety decision.\n"
        "- **`/rviz2`** displays ROS 2 information for a person. It is a support tool, not the robot's controller.\n"
        "- **`/course_evidence_collector`** records selected information for the lab guide. It is also a support tool."
    )

    st.markdown("**2A. List the running programs**")
    st.code("ros2 node list", language="bash")
    st.write("Find the four names above in the output. Other support nodes may also appear.")
    _mark_observation(st, checks, "node_list", CHECK_LABELS["node_list"])

    st.markdown("**2B. Inspect the safety decision**")
    st.code("ros2 node info /course_cmd_vel_guard", language="bash")
    st.write(
        "Look only at the **Subscribers** and **Publishers** sections. You should find that the guard "
        "subscribes to `/student_cmd_vel` and publishes to `/cmd_vel`. Subscribing is its input. "
        "Publishing is its output."
    )
    st.info("proposed command `/student_cmd_vel`  →  command guard  →  approved command `/cmd_vel`")
    _mark_observation(st, checks, "guard_info", CHECK_LABELS["guard_info"])

    st.markdown("**2C. Inspect the connection to the simulator**")
    st.code("ros2 node info /ros_gz_bridge", language="bash")
    st.write(
        "This node has a long list because it translates several kinds of information. Do not try to "
        "understand every entry. Find `/scan` and `/odom` among its outputs, and `/cmd_vel` among its inputs."
    )
    _mark_observation(st, checks, "bridge_info", CHECK_LABELS["bridge_info"])

    st.subheader("Step 3: Learn the five topic names used in this lab")
    st.write(
        "A ROS message type describes the fields inside a message. The full type names are shown for "
        "recognition only. You are not expected to memorize them."
    )
    for name in ("/scan", "/odom", "/student_cmd_vel", "/cmd_vel", "/tf"):
        item = topics.get(name, {})
        type_name = ", ".join(item.get("types", [])) or "not currently visible"
        st.markdown(f"**`{name}`**: {TOPIC_MEANINGS[name]}  \nROS type: `{type_name}`")

    st.markdown(
        "**New vocabulary**\n\n"
        "- **LiDAR** measures distances around the robot using light. Its readings travel on `/scan`.\n"
        "- **Odometry** is the robot's changing estimate of where it is based on its motion. It travels on `/odom`.\n"
        "- **Twist** is the ROS message format used for driving speed. Linear speed means forward or backward, and angular speed means turning. `/student_cmd_vel` uses Twist.\n"
        "- **TwistStamped** contains the same driving values plus timing information. The simulator bridge expects this format on `/cmd_vel`.\n"
        "- **`cmd_vel`** is short for command velocity.\n"
        "- **TF** describes how coordinate frames are positioned relative to one another. Week 3 will study frames in detail."
    )

    st.markdown("**3A. Inspect a sensor stream**")
    st.code("ros2 topic info /scan --verbose", language="bash")
    st.write(
        "Find `/ros_gz_bridge` under publishers and `/course_evidence_collector` under subscribers. "
        "This confirms the example graph shown at the beginning of the mission."
    )
    _mark_observation(st, checks, "scan_info", CHECK_LABELS["scan_info"])

    st.code("ros2 topic echo /scan --once", language="bash")
    st.write(
        "The command waits for one sensor message and then stops. Find the `ranges` field. Its long list "
        "contains distance measurements in meters around the robot. You do not need to interpret every number."
    )
    _mark_observation(st, checks, "scan_message", CHECK_LABELS["scan_message"])
    text_response(
        st,
        "mission_1.scan_observation",
        "Record one thing you noticed in the /scan message. Sentence starter: I found ___, which represents ___ .",
        height=80,
    )

    st.markdown("**3B. Compare the proposed and approved command channels**")
    st.code(
        "ros2 topic info /student_cmd_vel --verbose\n"
        "ros2 topic info /cmd_vel --verbose",
        language="bash",
    )
    st.write(
        "The first topic is waiting for a student command, so it may have zero publishers right now. "
        "The guard subscribes to it. The guard then publishes the approved command on `/cmd_vel`, and "
        "the simulator bridge subscribes so the virtual wheels can respond."
    )
    _mark_observation(st, checks, "command_topics", CHECK_LABELS["command_topics"])

    completed_checks = sum(bool(checks.get(key)) for key in GUIDED_CHECKS)
    set_response(st, "mission_1.guided_checks", checks)
    st.progress(completed_checks / len(GUIDED_CHECKS), text=f"Guided terminal observations: {completed_checks} of {len(GUIDED_CHECKS)}")
    missing = [CHECK_LABELS[key] for key in GUIDED_CHECKS if not checks.get(key)]
    if missing:
        st.info("Next observation to complete: " + missing[0])

    st.subheader("Step 4: Connect the graph to sense, decide, and act")
    st.write(
        "The same component can contribute to more than one part of the loop, so a single label does "
        "not always describe everything a component does. In this system:"
    )
    st.markdown(
        "1. **Sense:** Gazebo simulates LiDAR. The bridge publishes its readings on `/scan`.\n"
        "2. **Decide:** The command guard checks proposed movement. In Mission 3, your own behavior node will make a decision from `/scan`.\n"
        "3. **Act:** The bridge carries `/cmd_vel` into Gazebo, where the simulated wheels move.\n"
        "4. **Support:** RViz helps a person see the data, and the evidence collector saves selected results."
    )
    st.subheader("Step 5: Explain what you now understand")
    st.write("Each prompt below can be answered entirely from the worked examples above.")
    text_response(
        st,
        "mission_1.graph_explanation",
        "In your own words, what is a ROS 2 graph? Include one node and one topic from this mission. Sentence starter: A ROS 2 graph shows...",
    )
    text_response(
        st,
        "mission_1.command_path_explanation",
        "Why are /student_cmd_vel and /cmd_vel separate? Sentence starter: A proposed command travels on... The guard... Then...",
    )
    text_response(
        st,
        "mission_1.tools_explanation",
        "How are Gazebo and RViz different? Sentence starter: Gazebo is responsible for... while RViz is responsible for...",
    )

    check = evaluate(graph, st.session_state.get("responses", {}))
    render_check(st, check)
    current_id = evidence_id(stable_graph(graph), mission_responses(st.session_state.get("responses", {})))
    checked_id = st.session_state.get("checked_evidence_ids", {}).get("mission_1")
    if check.passed and checked_id != current_id:
        if st.button("Check and save Mission 1", type="primary"):
            evidence = {
                "evidence_id": current_id,
                "graph": graph,
                "stable_graph": stable_graph(graph),
                "check": [item.__dict__ for item in check.requirements],
            }
            save_mission("mission_1", evidence, st.session_state.get("responses", {}))
            complete_mission(st, "mission_1", current_id)
            st.rerun()
    if check.passed and checked_id == current_id:
        st.success("Mission 1 is saved.")
        if st.button("Continue to Mission 2", type="primary"):
            set_stage(st, "mission_2")
