#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
python3 "$LAB_ROOT/scripts/preflight.py"
