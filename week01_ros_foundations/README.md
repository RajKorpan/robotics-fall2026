# Week 1: Discovering a Robot Through ROS 2

This individual lab teaches ROS 2 by having each student inspect, control, and extend a simulated TurtleBot3 system. Week 1 includes the one-time setup of the shared course container, but installation troubleshooting is not the graded learning objective.

## Learning sequence

1. **Robot systems:** predict how sensing, decision, and actuation components communicate.
2. **Preflight:** verify a supplied ROS 2 Jazzy environment.
3. **Mission 1 — Observe:** inspect nodes, topics, message types, and graph relationships.
4. **Mission 2 — Control:** predict and execute straight, rotational, and curved velocity commands.
5. **Mission 3 — Create behavior:** implement and test a LiDAR-based obstacle-stop node.
6. **Final synthesis:** explain why the robot is a system of interacting components.

## Supported environment

The recommended environment is the shared course Docker image on Windows, macOS, or Linux. It contains Ubuntu 24.04, ROS 2 Jazzy, TurtleBot3, Gazebo, RViz, colcon, and the Streamlit dependencies. Students configure it once in this lab and reuse it for Weeks 3, 6, 8, 9, and 11.

Native Ubuntu 24.04 with ROS 2 Jazzy remains a supported performance fallback. Native ROS installation on Windows and macOS is not part of the supported course workflow.

The ROS packages are deliberately separated from the Streamlit application. ROS writes machine-readable evidence to `runtime/evidence/`; Streamlit reads that evidence and creates the durable `student_submission/` record.

## One-time student setup — Windows, macOS, or Linux

Follow the complete platform instructions in [`../ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md). In summary:

1. Install Docker Desktop on Windows/macOS, or Docker Engine plus Compose on Linux.
2. Clone this repository.
3. From the repository root, build the shared image and all six ROS workspaces.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ros_course.ps1 setup
.\scripts\ros_course.ps1 lab week01_ros_foundations
```

macOS/Linux:

```bash
chmod +x scripts/ros_course.sh
./scripts/ros_course.sh setup
./scripts/ros_course.sh lab week01_ros_foundations
```

Open the browser desktop at `http://localhost:6080/vnc.html?autoconnect=1&resize=remote` and the guide at `http://localhost:8501`. The first command downloads the course environment and builds all later ROS labs; do not repeat it every week.

Inside the browser desktop's Week 1 terminal, verify the environment:

```bash
bash scripts/course_preflight.sh
```

## Run the lab after initial setup

Start or reopen Week 1 from the host:

```powershell
.\scripts\ros_course.ps1 lab week01_ros_foundations
```

or on macOS/Linux:

```bash
./scripts/ros_course.sh lab week01_ros_foundations
```

In the browser desktop terminal:

```bash
bash scripts/launch_lab.sh
```

The course launcher already sources ROS, selects `ROS_DOMAIN_ID=24`, sets the TurtleBot3 model, changes into the lab directory, and starts Streamlit.

## Mission 3 starter behavior

The files below are intentionally incomplete:

- `ros2_ws/src/week01_behavior/week01_behavior/decision.py`
- `ros2_ws/src/week01_behavior/test/test_decision.py`

Students implement the pure decision helpers and may add tests. The ROS wrapper already includes parameters, a subscriber, a publisher, command bounding, and a stale-scan watchdog so students can focus on the publish/subscribe behavior.

Run its checks with:

```bash
bash scripts/evaluate_behavior.sh
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
