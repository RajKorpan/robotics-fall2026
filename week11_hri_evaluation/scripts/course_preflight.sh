#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
source /opt/ros/jazzy/setup.bash
echo "Building Lab 10 ROS package"
(cd ros2_ws && colcon build --symlink-install --build-base build_hri --install-base install_hri --packages-select course_hri)
if ! /opt/course-venv/bin/python -c 'from importlib.metadata import version; from pocketsphinx import Decoder; assert version("pocketsphinx") == "5.1.0"' 2>/dev/null; then
  CMAKE_BUILD_PARALLEL_LEVEL=2 /opt/course-venv/bin/python -m pip install -r requirements.txt
fi
/opt/course-venv/bin/python -c 'from speech import make_decoder; make_decoder(); print("Local speech decoder ready")'
source scripts/ros_env.sh
ros2 pkg prefix course_hri
echo "Lab 10 software is ready. Start the world using bash scripts/launch_handover.sh"
