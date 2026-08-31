# Week 6 — SLAM and Localization

An individual ROS 2 and Streamlit lab in which students operate established SLAM and localization systems, evaluate their output, and reason about when a robot can justifiably claim to know where it is. Students do **not** implement SLAM from scratch.

## Learning sequence

1. **Concepts:** connect LiDAR, odometry, TF, occupancy grids, loop closure, pose distributions, and covariance.
2. **Preflight:** verify a supplied ROS 2 Jazzy environment.
3. **Mission 1 — Build a map:** teleoperate through an unknown simulated environment, save the map, and analyze coverage and structural quality.
4. **Mission 2 — Compare strategies:** remap the same world using a different exploration strategy, then compare coverage, fragmentation, clipping, and loop-closure evidence.
5. **Mission 3 — Localize:** run AMCL against the saved map with a good initial pose, an incorrect pose, an ambiguous location, and a degraded scan.
6. **Final synthesis:** answer what it means for the robot to “know where it is” using evidence from the runs.

## Shared ROS environment

Use the course container configured once in Week 1. It already contains ROS 2 Jazzy, TurtleBot3 simulation/teleoperation, SLAM Toolbox, Navigation2, map server, AMCL, Gazebo, RViz, and Streamlit on Windows, macOS, and Linux. See [`../ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md). Native Ubuntu 24.04 remains an optional performance fallback.

The package and command choices follow the current [TurtleBot3 simulation and SLAM workflow](https://emanual.robotis.com/docs/en/platform/turtlebot3/slam_simulation/) and [Nav2 map-server interface](https://docs.ros.org/en/jazzy/p/nav2_map_server/).

## Instructor/native fallback setup

Install the ROS dependencies, clone/build TurtleBot3 Jazzy simulation if it is not distributed on the course image, then build the supplied package:

```bash
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox python3-colcon-common-extensions
cd week06_slam_localization/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
cd ..
python3 -m pip install --user -r requirements.txt
chmod +x scripts/*.sh
```

The official TurtleBot3 instructions describe the additional Jazzy source packages required when TurtleBot3 is not preinstalled: [TurtleBot3 Quick Start](https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/).

## Run in the shared course container

Windows:

```powershell
.\scripts\ros_course.ps1 lab week06_slam_localization
```

macOS/Linux:

```bash
./scripts/ros_course.sh lab week06_slam_localization
```

Then, in the browser desktop terminal:

```bash
bash scripts/course_preflight.sh
```

The guide is at `http://localhost:8501`. The launcher selects `ROS_DOMAIN_ID=26`. The Streamlit guide provides the exact commands for each mission. `scripts/launch_mapping.sh` starts the simulation and asynchronous SLAM. `scripts/launch_localization.sh` starts normal or degraded-scan localization. The supplied map analyzer and localization recorder produce the JSON evidence consumed by the guide.

## Safety and experimental controls

- Work only in simulation for this lab.
- Stop the robot before switching terminal focus.
- Do not run two Gazebo worlds or two localization systems in the same ROS domain.
- Restart the simulator and SLAM/localization between controlled trials.
- Use approximately equal mapping durations when comparing strategies.
- Never edit the saved PGM image or evidence JSON by hand.

## Submission

This is an **individual lab**. Submit the complete `student_submission/` directory and the individual Git commit. The folder contains:

- student identity and autosaved responses;
- two map YAML/image pairs, map-analysis JSON files, and RViz screenshots;
- four localization trial JSON files and screenshots from at least two conditions;
- mission explanations and quantitative evidence; and
- `manifest.json`.

```bash
git add student_submission
git commit -m "Submit Week 6 SLAM and localization lab"
git push
```

## Maintainer verification

The ROS-independent components can be tested on any supported Python machine:

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

Full integration requires ROS 2 Jazzy:

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
colcon test
colcon test-result --verbose
```
