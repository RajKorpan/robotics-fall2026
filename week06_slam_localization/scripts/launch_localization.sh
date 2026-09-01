#!/usr/bin/env bash
set -eo pipefail
if [[ $# -lt 1 ]]; then echo "Usage: $0 /absolute/path/to/map.yaml [normal|degraded]"; exit 2; fi
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
set -u
export TURTLEBOT3_MODEL=burger
ros2 launch course_slam_tools localization.launch.py map:="$1" degraded:="${2:-normal}"
