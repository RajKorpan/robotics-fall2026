# Week 3: Motion, Frames, and AI-Assisted ROS Development

This individual lab moves from raw ROS velocity commands to reasoning about pose, coordinate frames, and software correctness. Students must preserve an AI assistant's original output, identify its assumptions and problems, modify it, and justify the final program with tests.

## Learning sequence

1. Explore the planar motion model.
2. Predict and execute three motion sequences.
3. Compare predictions with observed pose.
4. Inspect `odom`, `base_link`, and `base_scan` transforms.
5. Transform points and diagnose frame errors.
6. Use an AI assistant for an individually assigned motion-pattern node.
7. Preserve the original output, test it, revise it, and explain why the final code is correct.

## Supported environment

- Ubuntu 24.04
- ROS 2 Jazzy
- TurtleBot3 simulation packages
- Gazebo and RViz
- `tf2_ros` and `tf2_tools`
- Python 3 using the ROS system interpreter

## Setup and run

```bash
cd week03_motion_frames_ai
python3 -m pip install --user -r requirements.txt
chmod +x scripts/*.sh
export ROS_DOMAIN_ID=24
./scripts/course_preflight.sh
```

Launch ROS in one terminal:

```bash
export ROS_DOMAIN_ID=24
./scripts/launch_lab.sh
```

Launch the guide in another:

```bash
python3 -m streamlit run app.py
```

Use a distinct `ROS_DOMAIN_ID` for every simultaneously running student or computer.

## Mission commands

Motion sequences are hidden in the app until predictions are locked. The underlying tools are:

```bash
ros2 run course_motion_tools run_sequence --ros-args -p sequence_id:=straight
ros2 run course_motion_tools run_sequence --ros-args -p sequence_id:=turn_then_drive
ros2 run course_motion_tools run_sequence --ros-args -p sequence_id:=arc
ros2 run course_motion_tools frame_probe
```

## AI-assisted mission

Students receive one deterministic assignment based on course ID: a rounded rectangle, L path, or alternating arcs. Streamlit permanently records the specification, original prompt, and original output before implementation.

Students edit:

```text
ros2_ws/src/week03_pattern/week03_pattern/pattern.py
ros2_ws/src/week03_pattern/week03_pattern/pattern_node.py
ros2_ws/src/week03_pattern/test/test_pattern.py
```

After building, run and evaluate the assigned pattern:

```bash
python3 scripts/run_assigned_pattern.py
./scripts/evaluate_ai_pattern.sh
```

The evaluator checks test count, velocity bounds, pattern geometry, a completed ROS run, final stop behavior, and whether the final source differs from the preserved AI output.

## Maintainer verification

Without ROS:

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

In the ROS image:

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
colcon test
colcon test-result --verbose
```

The student pattern starter intentionally fails its tests until implemented.

## Submission

The generated `student_submission/` contains mission evidence, source snapshots, the immutable AI record, a source diff, individual explanations, and a manifest.

```bash
git add student_submission ros2_ws/src/week03_pattern
git commit -m "Submit Week 3 motion, frames, and AI lab"
git push
```

