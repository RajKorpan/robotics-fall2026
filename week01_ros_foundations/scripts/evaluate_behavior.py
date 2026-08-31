from __future__ import annotations

import importlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "ros2_ws" / "src" / "week01_behavior"
sys.path.insert(0, str(PACKAGE_ROOT))


def run_scenario(name, function) -> dict:
    try:
        actual, expected = function()
        return {"passed": actual == expected, "actual": actual, "expected": expected}
    except Exception as error:
        return {"passed": False, "actual": f"{type(error).__name__}: {error}", "expected": "safe result"}


def main() -> None:
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(PACKAGE_ROOT / "test"), "-v"],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    decision = importlib.import_module("week01_behavior.decision")
    angle_min = -0.3
    increment = 0.1
    clear = [2.0] * 7
    outside = [0.8] * 7
    inside = [0.3] * 7
    invalid = [math.nan, math.inf, math.nan, math.inf, math.nan, math.inf, math.nan]

    def command(ranges):
        distance = decision.front_distance(ranges, angle_min, increment, 0.15)
        return decision.decide_velocity(distance, 0.5, 0.08)

    scenarios = {
        "clear_path": run_scenario("clear_path", lambda: (command(clear), 0.08)),
        "outside_threshold": run_scenario("outside_threshold", lambda: (command(outside), 0.08)),
        "inside_threshold": run_scenario("inside_threshold", lambda: (command(inside), 0.0)),
        "invalid_scan": run_scenario("invalid_scan", lambda: (command(invalid), 0.0)),
        "stale_scan": run_scenario("stale_scan", lambda: (decision.decide_velocity(None, 0.5, 0.08), 0.0)),
    }
    outputs = [value.get("actual") for value in scenarios.values()]
    command_bounded = all(isinstance(value, (int, float)) and 0.0 <= value <= 0.18 for value in outputs)
    graph_path = ROOT / "runtime" / "evidence" / "graph_snapshot.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8")) if graph_path.exists() else {}
    ros_node_verified = any("obstacle_guard" in str(node.get("name", node)) for node in graph.get("nodes", []))
    payload = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "unit_tests_passed": tests.returncode == 0,
        "unit_test_output": tests.stdout + tests.stderr,
        "command_bounded": command_bounded,
        "ros_node_verified": ros_node_verified,
        "scenarios": scenarios,
    }
    output = ROOT / "runtime" / "evidence" / "behavior_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(tests.stdout + tests.stderr)
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if tests.returncode == 0 and command_bounded and all(x["passed"] for x in scenarios.values()) else 1)


if __name__ == "__main__":
    main()

