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

## Shared ROS environment

Use the course container configured once in Week 1; do not reinstall ROS or Python packages. It provides ROS 2 Jazzy, TurtleBot3, Gazebo, RViz, `tf2_ros`, `tf2_tools`, and Streamlit on Windows, macOS, and Linux. See [`../ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md). Native Ubuntu 24.04 remains an optional performance fallback.

## Start the lab

```powershell
.\scripts\ros_course.ps1 lab week03_motion_frames_ai
```


## Required final reflection

After the technical work, complete the individual [final reflection](../FINAL_REFLECTION.md). Respond to any or all of the five prompts in 1–300 words. A blank response or a response over 300 words cannot finalize the submission. The app saves the response as `student_submission/final_reflection.md`, separate from technical syntheses and mission explanations.


or on macOS/Linux:

```bash
./scripts/ros_course.sh lab week03_motion_frames_ai
```

The guide opens at `http://localhost:8501`. In the browser desktop terminal, run:

```bash
bash scripts/course_preflight.sh
bash scripts/launch_lab.sh
```

The shared launcher selects `ROS_DOMAIN_ID=25` and sources this lab's built workspace.

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
bash scripts/evaluate_ai_pattern.sh
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
