#!/usr/bin/env bash
set -eo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
set -u
export TURTLEBOT3_MODEL=burger
export WEEK03_EVIDENCE_DIR="$LAB_ROOT/runtime/evidence"
ros2 launch course_robot_bringup week03.launch.py
