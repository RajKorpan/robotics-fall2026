from __future__ import annotations

from lab.navigation import set_stage
from lab.ui import choice_response, text_response


def render(st) -> None:
    st.title("Part 3: What ROS 2 provides")
    st.write(
        "ROS 2 is robotics middleware—not a traditional operating system. It provides libraries, "
        "conventions, command-line tools, visualization, package workflows, and communication so "
        "robot components can run concurrently and remain inspectable and replaceable."
    )

    st.subheader("Core concepts")
    middleware = choice_response(
        st,
        "part_3.middleware",
        "Which statement best describes ROS 2?",
        [
            "It replaces Windows, macOS, or Linux",
            "It is middleware that helps robot programs communicate and be developed as components",
            "It is only a robot simulator",
        ],
    )
    node = choice_response(st, "part_3.node", "A running obstacle-guard program is a", ["Node", "Topic", "Message", "Service"])
    topic = choice_response(st, "part_3.topic", "The named channel /scan is a", ["Node", "Topic", "Message", "Service"])
    message = choice_response(st, "part_3.message", "sensor_msgs/msg/LaserScan defines a", ["Node", "Topic", "Message", "Service"])
    service = choice_response(st, "part_3.service", "A reset-simulation request followed by one response is a", ["Node", "Topic", "Message", "Service"])

    st.subheader("Predict the ROS graph")
    st.code(
        "teleoperation or behavior node\n"
        "        ↓ publishes\n"
        " /student_cmd_vel (Twist)\n"
        "        ↓ subscribes\n"
        " command guard → /cmd_vel → simulated robot\n"
        "                         ├→ /scan → behavior / RViz\n"
        "                         └→ /odom → evidence / visualization"
    )
    sensor_information = text_response(st, "part_3.sensor_information", "What information must pass from a sensor node to a behavior node?")
    command_information = text_response(st, "part_3.command_information", "What information must pass from a behavior node toward the motion controller?")
    service_difference = text_response(st, "part_3.service_difference", "Why is a service a better match for reset simulation than a continuously published sensor topic?")
    rviz = choice_response(
        st,
        "part_3.rviz_closes",
        "If RViz closes, should the robot necessarily stop?",
        ["Yes", "No", "It depends on RViz's graph connections"],
    )
    sensor_stops = text_response(st, "part_3.sensor_stops", "What should a safe behavior do if sensor messages stop arriving?")
    robot_definition = text_response(st, "part_3.robot_definition", "Which pieces together make up the robot system in this lab?")
    diagnosis = text_response(
        st,
        "part_3.graph_diagnosis",
        "The command node publishes but the robot does not move. Which node, topic, message type, or connection would you inspect first, and why?",
        height=130,
    )

    facts_correct = (
        middleware == "It is middleware that helps robot programs communicate and be developed as components"
        and node == "Node"
        and topic == "Topic"
        and message == "Message"
        and service == "Service"
        and rviz in {"No", "It depends on RViz's graph connections"}
    )
    written_complete = all(
        len(value.strip()) >= 40
        for value in (sensor_information, command_information, service_difference, sensor_stops, robot_definition, diagnosis)
    )
    if any((middleware, node, topic, message, service, rviz)) and not facts_correct:
        st.warning("Review the middleware and communication definitions before continuing.")
    if st.button("Continue to environment preflight", type="primary", disabled=not (facts_correct and written_complete)):
        set_stage(st, "preflight")
