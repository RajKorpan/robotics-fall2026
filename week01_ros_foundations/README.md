# Week 1: Discovering a Robot Through ROS 2

This individual lab teaches ROS 2 by having each student inspect, control, and extend a simulated TurtleBot3 system. Installation is treated as a precondition rather than the learning objective.

## Learning sequence

1. **Robot systems:** predict how sensing, decision, and actuation components communicate.
2. **Preflight:** verify a supplied ROS 2 Jazzy environment.
3. **Mission 1 — Observe:** inspect nodes, topics, message types, and graph relationships.
4. **Mission 2 — Control:** predict and execute straight, rotational, and curved velocity commands.
5. **Mission 3 — Create behavior:** implement and test a LiDAR-based obstacle-stop node.
6. **Final synthesis:** explain why the robot is a system of interacting components.

## Supported environment

- Ubuntu 24.04
- ROS 2 Jazzy
- TurtleBot3 simulation packages
- Gazebo and RViz
- Python 3 using the ROS system interpreter

The ROS packages are deliberately separated from the Streamlit application. ROS writes machine-readable evidence to `runtime/evidence/`; Streamlit reads that evidence and creates the durable `student_submission/` record.

## First-time instructor setup

Install ROS 2 Jazzy, TurtleBot3 simulation dependencies, and the Python requirements. Then:

```bash
cd week01_ros_foundations
python3 -m pip install --user -r requirements.txt
chmod +x scripts/*.sh
export ROS_DOMAIN_ID=24
./scripts/course_preflight.sh
```

Use a unique `ROS_DOMAIN_ID` for each simultaneously running student or machine.

## Run the lab

Terminal 1:

```bash
cd week01_ros_foundations
export ROS_DOMAIN_ID=24
./scripts/launch_lab.sh
```

Terminal 2:

```bash
cd week01_ros_foundations
python3 -m streamlit run app.py
```

Open the local URL printed by Streamlit.

## Mission 3 starter behavior

The files below are intentionally incomplete:

- `ros2_ws/src/week01_behavior/week01_behavior/decision.py`
- `ros2_ws/src/week01_behavior/test/test_decision.py`

Students implement the pure decision helpers and may add tests. The ROS wrapper already includes parameters, a subscriber, a publisher, command bounding, and a stale-scan watchdog so students can focus on the publish/subscribe behavior.

Run its checks with:

```bash
./scripts/evaluate_behavior.sh
```

The evaluator exits unsuccessfully until the student implementation passes all required safety scenarios.

## Verification for maintainers

The application and mission validators can be checked without ROS:

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

ROS integration still requires an Ubuntu/ROS environment. Validate there with:

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
colcon test
colcon test-result --verbose
```

## Submission

The app generates:

```text
student_submission/
├── student.json
├── autosave/
│   ├── responses.json
│   └── responses.md
├── mission_1/
├── mission_2/
├── mission_3/
│   └── source/
└── manifest.json
```

Students submit their individual Git commit:

```bash
git add student_submission ros2_ws/src/week01_behavior
git commit -m "Submit Week 1 ROS foundations lab"
git push
```

## Instructor controls

The default local password is `ros-master`. Override it before distribution:

```bash
export WEEK01_INSTRUCTOR_PASSWORD="your-password"
```

Instructor navigation bypasses page order but does not fabricate mission evidence.

