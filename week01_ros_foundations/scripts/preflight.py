from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def command_succeeds(*command: str) -> bool:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main() -> None:
    evidence = ROOT / "runtime" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    packages = ("turtlebot3_gazebo", "course_cmd_vel_guard", "course_evidence_collector", "course_lab_tools")
    checks = [
        {"check": "ROS distribution", "passed": os.environ.get("ROS_DISTRO") == "jazzy", "detail": os.environ.get("ROS_DISTRO", "not sourced")},
        {"check": "ros2 command", "passed": shutil.which("ros2") is not None, "detail": shutil.which("ros2") or "missing"},
        {"check": "Course workspace", "passed": (ROOT / "ros2_ws" / "src").is_dir(), "detail": "ros2_ws/src"},
        {"check": "Evidence directory", "passed": os.access(evidence, os.W_OK), "detail": str(evidence)},
        {"check": "ROS_DOMAIN_ID", "passed": os.environ.get("ROS_DOMAIN_ID", "").isdigit(), "detail": os.environ.get("ROS_DOMAIN_ID", "not set")},
    ]
    for package in packages:
        checks.append({"check": f"Package: {package}", "passed": command_succeeds("ros2", "pkg", "prefix", package), "detail": package})
    payload = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "ready": all(check["passed"] for check in checks),
    }
    (evidence / "preflight.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for check in checks:
        print(f"{check['check']:<36} {'PASS' if check['passed'] else 'FAIL':<5} {check['detail']}")
    raise SystemExit(0 if payload["ready"] else 1)


if __name__ == "__main__":
    main()

