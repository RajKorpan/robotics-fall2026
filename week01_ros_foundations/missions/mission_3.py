from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from lab.models import RequirementResult, check_from_requirements


SCENARIOS = ("clear_path", "outside_threshold", "inside_threshold", "invalid_scan", "stale_scan")
EXPLANATION_KEYS = ("data_to_command", "missing_data_safety", "system_layers")


def _functions_are_implemented(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in ("front_distance", "decide_velocity"):
        function = functions.get(name)
        if function is None:
            return False
        for node in ast.walk(function):
            if not isinstance(node, ast.Raise):
                continue
            exception = node.exc
            if isinstance(exception, ast.Call):
                exception = exception.func
            if isinstance(exception, ast.Name) and exception.id == "NotImplementedError":
                return False
    return True


def evaluate(
    behavior: dict[str, Any],
    graph: dict[str, Any],
    responses: dict[str, Any],
    source_root: Path,
):
    scenarios = behavior.get("scenarios", {})
    scenario_count = sum(bool(scenarios.get(name, {}).get("passed")) for name in SCENARIOS)
    decision_path = source_root / "week01_behavior" / "decision.py"
    wrapper_path = source_root / "week01_behavior" / "obstacle_guard.py"
    student_test_path = source_root / "test" / "test_student_decision.py"
    decision_text = decision_path.read_text(encoding="utf-8") if decision_path.exists() else ""
    student_test_text = student_test_path.read_text(encoding="utf-8") if student_test_path.exists() else ""
    implementation_complete = (
        wrapper_path.exists()
        and _functions_are_implemented(decision_text)
    )
    student_test_complete = (
        len(student_test_text.strip()) >= 100
        and "test" in student_test_text
        and ("front_distance" in student_test_text or "decide_velocity" in student_test_text)
    )
    node_names = {str(node.get("name", node)) for node in graph.get("nodes", [])}
    node_visible = any("obstacle_guard" in name for name in node_names) or bool(behavior.get("ros_node_verified"))
    explanation_count = sum(
        len(str(responses.get(f"mission_3.{key}", "")).strip()) >= 40
        for key in EXPLANATION_KEYS
    )
    requirements = [
        RequirementResult(
            "implementation",
            "Both decision functions implemented",
            implementation_complete,
            "complete" if implementation_complete else "unfinished",
            "complete",
        ),
        RequirementResult(
            "student_test",
            "Student-created unit test present",
            student_test_complete,
            "complete" if student_test_complete else "missing or incomplete",
            "complete",
        ),
        RequirementResult(
            "tests",
            "All unit tests pass",
            bool(behavior.get("unit_tests_passed")),
            bool(behavior.get("unit_tests_passed")),
            "true",
        ),
        RequirementResult(
            "scenarios",
            "All five behavior situations pass",
            scenario_count == len(SCENARIOS),
            scenario_count,
            f"{len(SCENARIOS)}/{len(SCENARIOS)}",
        ),
        RequirementResult(
            "bounded",
            "Forward command remains within the safe limit",
            bool(behavior.get("command_bounded")),
            bool(behavior.get("command_bounded")),
            "true",
        ),
        RequirementResult(
            "node",
            "Obstacle guard verified as a running ROS 2 node",
            node_visible,
            node_visible,
            "true",
        ),
        RequirementResult(
            "explanations",
            "Three system explanations completed",
            explanation_count == len(EXPLANATION_KEYS),
            explanation_count,
            f"{len(EXPLANATION_KEYS)}/{len(EXPLANATION_KEYS)}",
        ),
    ]
    return check_from_requirements("Your sensor-based ROS 2 behavior passed its checks.", requirements)
