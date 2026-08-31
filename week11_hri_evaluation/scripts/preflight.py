#!/usr/bin/env python3
import os, shutil, subprocess, sys

REQUIRED = ("rclpy", "std_msgs", "geometry_msgs", "week11_hri_demo")


def main():
    checks = [("Python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0]), ("ROS 2 CLI", shutil.which("ros2") is not None, shutil.which("ros2") or "missing"), ("ROS_DISTRO is jazzy", os.getenv("ROS_DISTRO") == "jazzy", os.getenv("ROS_DISTRO", "unset"))]
    if shutil.which("ros2"):
        packages = set(subprocess.run(["ros2", "pkg", "list"], capture_output=True, text=True, check=False).stdout.splitlines()); checks.extend((f"Package {p}", p in packages, "found" if p in packages else "missing") for p in REQUIRED)
    for label, passed, actual in checks: print(f"[{'PASS' if passed else 'FAIL'}] {label}: {actual}")
    return 0 if all(x[1] for x in checks) else 1


if __name__ == "__main__": raise SystemExit(main())

