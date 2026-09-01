#!/usr/bin/env bash
set -e

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
cd "$LAB_ROOT/ros2_ws" || exit 1
colcon build --symlink-install || exit 1
source install/setup.bash
set -u
export WEEK01_EVIDENCE_DIR="$LAB_ROOT/runtime/evidence"
python3 "$LAB_ROOT/scripts/preflight.py"
