#!/usr/bin/env bash
set -eo pipefail
if [[ $# -lt 1 ]]; then echo "Usage: $0 path/to/map.yaml"; exit 2; fi
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
source ros2_ws/install/setup.bash
set -u
ros2 launch week09_nav_tools course_navigation.launch.py map:="$1"
