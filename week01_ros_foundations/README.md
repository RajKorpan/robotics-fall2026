# Week 1: Discovering a Robot Through ROS 2

This individual lab connects three conceptual foundations to a simulated TurtleBot3: why robotics software is difficult, how robot architectures organize sensing and action, and how ROS 2 implements modular communication. Week 1 includes the one-time setup of the shared course container, but installation troubleshooting is not the graded learning objective.

## Learning sequence

1. **Part 1 — Why robotics software is difficult:** manipulate toy examples of imperfect sensors, timing delays, distributed failures, and hardware slip.
2. **Part 2 — Robot software architectures:** watch the same scenario behave under reactive, behavior-based, deliberative, and hybrid control, then run a safety override.
3. **Part 3 — What ROS 2 provides:** follow topic messages, call a service, break graph connections, and try simulated ROS inspection commands.
4. **Preflight:** verify the shared ROS 2 Jazzy environment.
5. **Mission 1 — Observe:** learn the simulation and ROS graph vocabulary, then follow a guided tour of four nodes, key topics, and two communication paths.
6. **Mission 2 — Control:** predict and execute motion, then compare command timing and expected versus observed behavior.
7. **Mission 3 - Create behavior:** implement and test the decision functions used by a supplied LiDAR obstacle-stop ROS 2 node.
8. **Final synthesis:** connect the three parts to live evidence and the implemented behavior.

The first three parts are required, ungraded Streamlit tutorials. They contain demonstrations rather than quiz questions or written-response boxes. Exploration progress autosaves and is collected in `student_submission/foundations.md`.

## Supported environment

The recommended environment is the shared course Docker image on Windows, macOS, or Linux. It contains Ubuntu 24.04, ROS 2 Jazzy, TurtleBot3, Gazebo, RViz, colcon, and the Streamlit dependencies. Students configure it once in this lab and reuse it for Weeks 3, 6, 8, 9, and 11.

Native Ubuntu 24.04 with ROS 2 Jazzy remains a supported performance fallback. Native ROS installation on Windows and macOS is not part of the supported course workflow.

The ROS packages are deliberately separated from the Streamlit application. ROS writes machine-readable graph, timing, and behavior evidence to `runtime/evidence/`; Streamlit reads that evidence and creates the durable `student_submission/` record.

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

The decision file below is intentionally incomplete:

- `ros2_ws/src/week01_behavior/week01_behavior/decision.py`

Students implement the two pure decision helpers and create `test/test_student_decision.py`. The supplied `test/test_decision.py` provides additional checks. The ROS wrapper already includes parameters, a subscriber, a publisher, command bounding, and a stale-scan watchdog so students can focus on interpreting sensor data and making a safe move-or-stop decision.

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
├── foundations.md
├── final_reflection.md
├── autosave/
│   ├── responses.json
│   └── responses.md
├── mission_1/
│   └── ros_system_diagram.md
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


## Required final reflection

After the technical work, complete the individual [final reflection](../FINAL_REFLECTION.md). Respond to any or all of the five prompts in 1–300 words. A blank response or a response over 300 words cannot finalize the submission. The app saves the response as `student_submission/final_reflection.md`, separate from technical syntheses and mission explanations.
