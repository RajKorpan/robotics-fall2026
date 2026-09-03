from __future__ import annotations

from typing import Any

from lab.models import RequirementResult, check_from_requirements


REQUIRED_TOPICS = {
    "/scan": "sensor_msgs/msg/LaserScan",
    "/odom": "nav_msgs/msg/Odometry",
    "/student_cmd_vel": "geometry_msgs/msg/Twist",
    "/cmd_vel": "geometry_msgs/msg/TwistStamped",
}

GUIDED_CHECKS = (
    "node_list",
    "guard_info",
    "bridge_info",
    "scan_info",
    "scan_message",
    "command_topics",
)

SYNTHESIS_KEYS = (
    "graph_explanation",
    "command_path_explanation",
    "tools_explanation",
)


def _named_map(items: list[Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("name", "")): item
        for item in items
        if isinstance(item, dict) and str(item.get("name", ""))
    }


def stable_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Return topology only, excluding timestamps and changing sensor samples."""
    return {
        "nodes": sorted(str(item.get("name", item)) for item in graph.get("nodes", [])),
        "topics": sorted(
            (
                str(item.get("name", "")),
                tuple(sorted(str(value) for value in item.get("types", []))),
                tuple(sorted(str(value) for value in item.get("publishers", []))),
                tuple(sorted(str(value) for value in item.get("subscribers", []))),
            )
            for item in graph.get("topics", [])
            if isinstance(item, dict)
        ),
    }


def mission_responses(responses: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in responses.items()
        if key.startswith("mission_1.")
    }


def evaluate(graph: dict[str, Any], responses: dict[str, Any]):
    nodes = {str(item.get("name", item)) for item in graph.get("nodes", [])}
    topics = _named_map(graph.get("topics", []))

    required_nodes = {
        "/course_cmd_vel_guard",
        "/course_evidence_collector",
        "/ros_gz_bridge",
        "/rviz2",
    }
    required_topics_present = all(
        name in topics and expected in topics[name].get("types", [])
        for name, expected in REQUIRED_TOPICS.items()
    )
    endpoint_evidence = bool(
        topics.get("/scan", {}).get("publishers")
        and topics.get("/scan", {}).get("subscribers")
        and topics.get("/odom", {}).get("publishers")
        and topics.get("/student_cmd_vel", {}).get("subscribers")
        and topics.get("/cmd_vel", {}).get("publishers")
        and topics.get("/cmd_vel", {}).get("subscribers")
    )

    guided_checks = responses.get("mission_1.guided_checks", {})
    checks_complete = all(bool(guided_checks.get(key)) for key in GUIDED_CHECKS)
    scan_observation = len(str(responses.get("mission_1.scan_observation", "")).strip()) >= 30
    synthesis_complete = all(
        len(str(responses.get(f"mission_1.{key}", "")).strip()) >= 50
        for key in SYNTHESIS_KEYS
    )

    requirements = [
        RequirementResult("graph", "The running robot system was detected", bool(graph.get("captured_at")), "detected" if graph.get("captured_at") else "not detected", "detected"),
        RequirementResult("nodes", "The four guided components are running", required_nodes.issubset(nodes), len(required_nodes.intersection(nodes)), "4 of 4"),
        RequirementResult("topics", "The four guided communication channels are available", required_topics_present, len([name for name in REQUIRED_TOPICS if name in topics]), "4 of 4"),
        RequirementResult("endpoints", "The guide can see how the components are connected", endpoint_evidence, "connected" if endpoint_evidence else "connections still loading", "connected"),
        RequirementResult("guided_checks", "All six guided terminal observations are marked complete", checks_complete, sum(bool(guided_checks.get(key)) for key in GUIDED_CHECKS), "6 of 6"),
        RequirementResult("scan_observation", "The LiDAR observation is recorded", scan_observation, "complete" if scan_observation else "not yet", "complete"),
        RequirementResult(
            "synthesis",
            "The three scaffolded explanations are complete",
            synthesis_complete,
            sum(len(str(responses.get(f"mission_1.{key}", "")).strip()) >= 50 for key in SYNTHESIS_KEYS),
            "3 of 3",
        ),
    ]
    return check_from_requirements("You used a live ROS 2 graph to explain this robot system.", requirements)
