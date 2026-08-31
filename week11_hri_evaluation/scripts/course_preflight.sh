#!/usr/bin/env bash
set -u
source /opt/ros/jazzy/setup.bash
if [[ -f ros2_ws/install/setup.bash ]]; then source ros2_ws/install/setup.bash; fi
python3 scripts/preflight.py

