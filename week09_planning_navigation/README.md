# Week 9 — Planning and Human-Aware Navigation

An individual ROS 2 + Streamlit lab in which students use Nav2 to distinguish a feasible path from successful, context-appropriate navigation.

## Learning sequence

1. **System model:** connect map/localization, costmaps, planner, controller, sensors, recoveries, and motion.
2. **Preflight:** restore the Week 6 map, localize the robot, and verify Nav2 topics/actions in RViz.
3. **Mission 1 — Plan:** predict and request five paths; compare length, clearance, detours, and correctly rejected goals.
4. **Mission 2 — Navigate:** execute five controlled trials; measure success, completion time, traveled distance, recoveries, collisions, and near misses.
5. **Mission 3 — Human-aware redesign:** show that a collision-free baseline violates a scenario-specific personal-space rule, alter at least two costmap/behavior rules, and retest the same start and goal.
6. **Synthesis:** define successful navigation using geometric, empirical, and human-centered evidence.

Nav2 exposes path computation through [`ComputePathToPose`](https://docs.ros.org/en/ros2_packages/jazzy/api/nav2_msgs/action/ComputePathToPose.html) and goal execution through [`NavigateToPose`](https://docs.ros.org/en/ros2_packages/jazzy/api/nav2_msgs/action/NavigateToPose.html). Its costmap filters can annotate keepout/preferred regions and speed-restriction regions; see the official [costmap-filter tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_keepout_filter.html) and [Costmap Filter Info Server parameters](https://docs.nav2.org/configuration/packages/map_server/configuring-costmap-filter-info-server.html).

## Shared ROS environment

Use the course container configured once in Week 1. It provides ROS 2 Jazzy, TurtleBot3 simulation, RViz, Nav2, and Streamlit on Windows, macOS, and Linux. The Week 6 saved map persists through the repository bind mount. See [`../ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md).

## Instructor preparation

Before release, open `assets/scenarios/goals.json` and move the five goal poses onto the exact distributed map while retaining their identifiers and reachable/unreachable labels. Place the two simulated people described by `people.json` into the matching world. Confirm the baseline route passes within 0.75 m of the seated-person boundary without colliding, while a reasonable detour exists.

Provide:

- a canonical Week 6 map/world and initial pose for comparison;
- a complete TurtleBot3 Nav2 parameter file into which students can merge `config/human_aware_costmap_fragment.yaml`;
- keepout and speed-mask examples plus corresponding lifecycle-managed map/filter-info server launch nodes;
- a recorded demonstration dataset for students whose simulator cannot run reliably; and
- clear disclosure that course clearance/speed thresholds are scenario tests, not universal cultural norms.

Install and build:

```bash
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3-navigation2 \
  python3-colcon-common-extensions
cd week09_planning_navigation/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
cd ..
python3 -m pip install --user -r requirements.txt
chmod +x scripts/*.sh scripts/*.py
```

## Run the lab

Windows:

```powershell
.\scripts\ros_course.ps1 lab week09_planning_navigation
```

macOS/Linux:

```bash
./scripts/ros_course.sh lab week09_planning_navigation
```

In the browser desktop terminal:

```bash
bash scripts/course_preflight.sh
bash scripts/launch_navigation.sh /absolute/path/to/week06_map.yaml
```

The guide is at `http://localhost:8501`; the launcher selects `ROS_DOMAIN_ID=29` and sources the Week 9 workspace.

The launcher starts TurtleBot3 World plus its navigation launch using the supplied map. The instructor should adjust `course_navigation.launch.py` if the course distributes a different simulator/world.

## Human-aware configuration boundary

`config/human_aware_costmap_fragment.yaml` is intentionally a fragment. It must be merged into a complete robot-specific Nav2 parameter file. A working deployment also needs map-server and `CostmapFilterInfoServer` nodes for each mask. This makes the student artifact an explicit configuration redesign without silently replacing the robot's controller, footprint, topics, or other safety-relevant settings.

Students may use one or more of:

- keepout masks around people or seating areas;
- larger/context-sensitive inflation or a social cost layer;
- absolute or percentage speed masks near people;
- controller limits and an explicit stop/confirmation rule.

They must preserve a baseline, list every changed parameter/file, and compare the identical scenario and goal.

## Evidence format

ROS collectors append raw rows to JSON. `scripts/evaluate_evidence.py` adds metrics and pass/fail checks without ROS:

```bash
python3 scripts/evaluate_evidence.py plans runtime/evidence/plans_raw.json --output runtime/evidence/plans_checked.json
python3 scripts/evaluate_evidence.py navigation runtime/evidence/navigation_raw.json --output runtime/evidence/navigation_checked.json
python3 scripts/evaluate_evidence.py human-aware runtime/evidence/human_aware_raw.json --output runtime/evidence/human_aware_checked.json
```

For human-aware evidence, assemble:

```json
{
  "policy": {"required_clearance_m": 0.75, "maximum_nearby_speed_mps": 0.12},
  "baseline": {"scenario_id": "seated_person_corridor", "goal_id": "social_goal", "metrics": {"minimum_person_clearance_m": 0.10}},
  "redesign": {"scenario_id": "seated_person_corridor", "goal_id": "social_goal", "status": "succeeded", "metrics": {"minimum_person_clearance_m": 0.82, "maximum_speed_near_people_mps": 0.10}},
  "parameter_changes": ["added seated-person keepout region", "limited speed inside 1.2 m region"]
}
```

The supplied navigation recorder reports a clearly labeled LiDAR collision proxy. Use simulator contact data when available and explain the distinction; do not present a range threshold as ground-truth contact.

## Individual submission

Submit `student_submission/` and an individual Git commit containing:

- raw and checked plan/navigation/social JSON;
- RViz evidence for successful, rejected, recovered, baseline, and redesign cases;
- the actual merged Nav2 configuration and masks;
- the requested mission explanations and 200–300 word synthesis; and
- `manifest.json`.

## Maintainer checks

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

ROS integration additionally requires `colcon build --symlink-install` in `ros2_ws`.
