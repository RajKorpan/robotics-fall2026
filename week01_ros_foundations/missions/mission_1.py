from __future__ import annotations

from typing import Any

from lab.models import RequirementResult, check_from_requirements


REQUIRED_TOPICS = {
    "/scan": "sensor_msgs/msg/LaserScan",
    "/odom": "nav_msgs/msg/Odometry",
    "/student_cmd_vel": "geometry_msgs/msg/Twist",
}

REQUIRED_CONNECTION_ANSWERS = {
    "teleop_output": "/student_cmd_vel",
    "guard_input": "/student_cmd_vel",
    "guard_output": "/cmd_vel",
    "lidar_output": "/scan",
    "odometry_output": "/odom",
}

REFLECTION_KEYS = (
    "node_vs_topic",
    "sense_decide_act",
    "multiple_subscribers",
    "teleop_change",
    "rviz_role",
    "service_vs_topic",
    "middleware_evidence",
    "failure_diagnosis",
    "architecture_observation",
)


def _topic_map(graph: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for topic in graph.get("topics", []):
        if isinstance(topic, dict):
            result[str(topic.get("name", ""))] = [str(value) for value in topic.get("types", [])]
    return result


def evaluate(graph: dict[str, Any], responses: dict[str, Any]):
    topics = _topic_map(graph)
    nodes = graph.get("nodes", [])
    node_roles = responses.get("mission_1.node_roles", {})
    pipeline_roles = responses.get("mission_1.pipeline_roles", {})
    connections = responses.get("mission_1.connections", {})
    topic_types = responses.get("mission_1.topic_types", {})
    topic_evidence = all(
        name in topics and expected in topics[name]
        for name, expected in REQUIRED_TOPICS.items()
    )
    student_types = all(topic_types.get(name) == expected for name, expected in REQUIRED_TOPICS.items())
    connection_count = sum(
        connections.get(key) == expected for key, expected in REQUIRED_CONNECTION_ANSWERS.items()
    )
    services = graph.get("services", [])
    service_example = responses.get("mission_1.service_example", {})
    service_identified = bool(
        str(service_example.get("name", "")).strip()
        and str(service_example.get("type", "")).strip()
        and str(service_example.get("purpose", "")).strip()
    )
    reflections_complete = all(str(responses.get(f"mission_1.{key}", "")).strip() for key in REFLECTION_KEYS)
    requirements = [
        RequirementResult("graph", "Live ROS graph captured", bool(graph.get("captured_at")), graph.get("captured_at", "missing"), "timestamp present"),
        RequirementResult("nodes", "At least five nodes observed", len(nodes) >= 5, len(nodes), ">= 5"),
        RequirementResult("topics", "Required topics and types present", topic_evidence, sorted(topics), "scan, odom, student_cmd_vel"),
        RequirementResult("topic_types", "Student identifies the three message types", student_types, sum(topic_types.get(k) == v for k, v in REQUIRED_TOPICS.items()), "3/3"),
        RequirementResult("roles", "At least five nodes classified", len([v for v in node_roles.values() if v]), len([v for v in node_roles.values() if v]), ">= 5"),
        RequirementResult("pipeline_roles", "At least five nodes mapped to sense, decide, act, or support", len([v for v in pipeline_roles.values() if v]), len([v for v in pipeline_roles.values() if v]), ">= 5"),
        RequirementResult("connections", "System communication paths are correct", connection_count == len(REQUIRED_CONNECTION_ANSWERS), connection_count, f"{len(REQUIRED_CONNECTION_ANSWERS)}/{len(REQUIRED_CONNECTION_ANSWERS)}"),
        RequirementResult("services", "ROS services observed in the live graph", bool(services), len(services), ">= 1"),
        RequirementResult("service_example", "One service, type, and likely purpose documented", service_identified, "complete" if service_identified else "incomplete", "complete"),
        RequirementResult("reflections", "Mission reflections completed", reflections_complete, "complete" if reflections_complete else "incomplete", "complete"),
    ]
    return check_from_requirements("You identified how the simulated robot's components communicate.", requirements)
