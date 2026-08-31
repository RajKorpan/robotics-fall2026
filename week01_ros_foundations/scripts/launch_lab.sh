#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
export TURTLEBOT3_MODEL=burger
export WEEK01_EVIDENCE_DIR="$LAB_ROOT/runtime/evidence"
ros2 launch course_robot_bringup week01.launch.py

