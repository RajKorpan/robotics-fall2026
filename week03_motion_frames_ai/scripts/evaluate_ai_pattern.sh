#!/usr/bin/env bash
set -e
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
cd "$LAB_ROOT/ros2_ws" || exit 1
colcon build --packages-select week03_pattern --symlink-install || exit 1
source install/setup.bash
set -u
colcon test --packages-select week03_pattern
colcon test-result --verbose
export WEEK03_EVIDENCE_DIR="$LAB_ROOT/runtime/evidence"
python3 "$LAB_ROOT/scripts/evaluate_ai_pattern.py"
