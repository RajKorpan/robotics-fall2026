#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
set -u
CONFIG="${1:-$(pwd)/ros2_ws/src/week11_hri_demo/config/baseline.yaml}"
ros2 launch week11_hri_demo interaction.launch.py config:="$CONFIG" motion_enabled:=false
