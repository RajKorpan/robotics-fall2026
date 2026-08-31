#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys


REQUIRED = ("nav2_msgs", "nav2_bringup", "nav2_costmap_2d", "turtlebot3_gazebo", "turtlebot3_navigation2")


def main() -> int:
    checks = []
    checks.append(("Python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0]))
    checks.append(("ROS 2 CLI", shutil.which("ros2") is not None, shutil.which("ros2") or "not found"))
    checks.append(("ROS_DISTRO is jazzy", os.getenv("ROS_DISTRO") == "jazzy", os.getenv("ROS_DISTRO", "unset")))
    checks.append(("TURTLEBOT3_MODEL set", bool(os.getenv("TURTLEBOT3_MODEL")), os.getenv("TURTLEBOT3_MODEL", "unset")))
    if shutil.which("ros2"):
        packages = set(subprocess.run(["ros2", "pkg", "list"], capture_output=True, text=True, check=False).stdout.splitlines())
        checks.extend((f"ROS package {name}", name in packages, "found" if name in packages else "missing") for name in REQUIRED)
    for label, passed, actual in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {label}: {actual}")
    return 0 if all(passed for _, passed, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

