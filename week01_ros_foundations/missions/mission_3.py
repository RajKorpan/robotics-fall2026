from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.models import RequirementResult, check_from_requirements


SCENARIOS = ("clear_path", "outside_threshold", "inside_threshold", "invalid_scan", "stale_scan")
REFLECTION_KEYS = (
    "decision_node",
    "received_information",
    "scan_assumptions",
    "missing_vs_clear",
    "hardware_limitation",
    "whole_system",
)


def evaluate(
    behavior: dict[str, Any],
    graph: dict[str, Any],
    responses: dict[str, Any],
    source_root: Path,
):
    scenarios = behavior.get("scenarios", {})
    scenario_count = sum(bool(scenarios.get(name, {}).get("passed")) for name in SCENARIOS)
    tests_passed = bool(behavior.get("unit_tests_passed"))
    command_bounded = bool(behavior.get("command_bounded"))
    source_files = (
        source_root / "week01_behavior" / "decision.py",
        source_root / "week01_behavior" / "obstacle_guard.py",
        source_root / "test" / "test_decision.py",
    )
    source_complete = all(path.exists() and path.stat().st_size > 100 for path in source_files)
    node_names = {
        str(node.get("name", node)) for node in graph.get("nodes", [])
    }
    node_visible = any("obstacle_guard" in name for name in node_names) or bool(behavior.get("ros_node_verified"))
    design = responses.get("mission_3.design", {})
    design_complete = all(str(design.get(key, "")).strip() for key in ("front_width", "stop_distance", "forward_speed", "invalid_policy", "stale_policy"))
    failure_investigation = len(str(responses.get("mission_3.failure_investigation", "")).strip()) >= 100
    reflections_complete = all(str(responses.get(f"mission_3.{key}", "")).strip() for key in REFLECTION_KEYS)
    requirements = [
        RequirementResult("design", "Behavior design completed before evaluation", design_complete, "complete" if design_complete else "incomplete", "complete"),
        RequirementResult("source", "Required source and test files present", source_complete, source_complete, "true"),
        RequirementResult("tests", "Unit tests pass", tests_passed, tests_passed, "true"),
        RequirementResult("scenarios", "Required behavior scenarios pass", scenario_count == len(SCENARIOS), scenario_count, f"{len(SCENARIOS)}/{len(SCENARIOS)}"),
        RequirementResult("bounded", "Velocity command is bounded", command_bounded, command_bounded, "true"),
        RequirementResult("node", "Obstacle guard verified as a ROS node", node_visible, node_visible, "true"),
        RequirementResult("failure", "Failure investigation documented", failure_investigation, len(str(responses.get("mission_3.failure_investigation", ""))), ">= 100 characters"),
        RequirementResult("reflections", "Mission reflections completed", reflections_complete, "complete" if reflections_complete else "incomplete", "complete"),
    ]
    return check_from_requirements("Your sensor-based ROS behavior passed its safety scenarios.", requirements)

