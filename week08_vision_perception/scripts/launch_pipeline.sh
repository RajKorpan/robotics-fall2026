#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then echo "Usage: $0 classical|learned [camera_topic] [false|true enable_behavior]"; exit 2; fi
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$LAB_ROOT/ros2_ws/install/setup.bash"
ros2 launch week08_perception pipeline.launch.py mode:="$1" camera_topic:="${2:-/camera/image_raw}" enable_behavior:="${3:-false}" model_path:="$LAB_ROOT/assets/models/detector.onnx" labels_path:="$LAB_ROOT/assets/models/labels.txt"
