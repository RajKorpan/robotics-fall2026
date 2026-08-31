# Week 11 — Human–Robot Interaction Evaluation

An individual ROS 2 + Streamlit lab organized around a complete formative design cycle:

> prototype → user test → evidence → redesign → matched retest

Students temporarily work in pairs so each can serve as the other's participant. All implementations, observations, analysis, artifacts, and submissions remain individual.

## Learning sequence

1. **Concepts:** intention visibility, feedback, listening clarity, predictability, recoverability, accessibility, and human control.
2. **Protocol and preflight:** establish voluntary participation, data minimization, stop authority, and a motion-disabled ROS test environment.
3. **Mission 1 — Prototype:** inspect and dry-run a stateful interaction that announces intent, approaches, listens, confirms, acts, times out safely, accepts correction/cancellation, and exposes an emergency stop.
4. **Mission 2 — Baseline evaluation:** run five scripted scenarios with one peer and record task outcomes, comprehension, feedback, recovery, predictability, access barriers, timing, and non-identifying notes.
5. **Mission 3 — Redesign and retest:** implement at least two evidence-based changes and repeat the same five scenarios with the same random participant code when possible.
6. **Synthesis:** explain what the evidence supports, what it does not support, and what should change next.

ROS topics are appropriate here because interaction status and commands are asynchronous streams shared by interface, robot, and recorder nodes; see the official ROS 2 [interfaces documentation](https://docs.ros.org/en/jazzy/How-To-Guides/Topics-Services-Actions.html). The prototype publishes velocity using the standard [`geometry_msgs/Twist`](https://docs.ros.org/en/jazzy/p/geometry_msgs/msg/Twist.html) message, but keeps it on `/hri/cmd_vel` and sets motion off during peer testing.

## Safety and participant protocol

This is a short classroom usability exercise, not human-subjects research and not evidence about a population. Follow `assets/protocol/participant_script.md`:

- participation is voluntary and may stop at any time;
- record only a random code beginning with `P-`;
- collect no name, demographic, disability, medical, audio, video, photo, or other identifying data;
- describe interface behavior, not participant traits;
- keep physical motion disabled unless the instructor explicitly supervises it; and
- each student uses and submits only their own evaluation data.

## Shared ROS environment

Use the course container configured once in Week 1. It provides ROS 2 Jazzy, colcon, and Streamlit on Windows, macOS, and Linux. No physical robot is required. See [`../ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md).

## Run

Windows:

```powershell
.\scripts\ros_course.ps1 lab week11_hri_evaluation
```

macOS/Linux:

```bash
./scripts/ros_course.sh lab week11_hri_evaluation
```

Then, in the browser desktop terminal:

```bash
bash scripts/course_preflight.sh
bash scripts/launch_interaction.sh
```

The guide is at `http://localhost:8501`; the launcher selects `ROS_DOMAIN_ID=31`, sources the Week 11 workspace, and keeps motion disabled by default.

Send commands from another sourced terminal:

```bash
ros2 topic pub --once /hri/command std_msgs/msg/String "{data: 'bring the blue cup'}"
ros2 topic pub --once /hri/command std_msgs/msg/String "{data: 'yes'}"
ros2 topic pub --once /hri/emergency_stop std_msgs/msg/Bool "{data: true}"
```

The prototype publishes:

```text
/hri/state       current interaction state
/hri/display     visible user-facing feedback
/hri/cmd_vel     isolated velocity proposal; zero when motion is disabled
```

It subscribes to `/hri/command`, the alternate `/hri/text_command`, and `/hri/emergency_stop`. Both command modalities enter the same state machine. The state/display topics use reliable, transient-local QoS so a newly opened display can receive the latest status. The command and stop inputs use ordinary reliable topic delivery.

## Evidence and redesign

Complete `assets/protocol/blank_trials.json` for the baseline. Each of the five rows must contain:

- task success;
- intent and listening comprehension;
- recovery without facilitator help;
- 1–5 predictability and feedback-clarity ratings;
- access barrier and safety-stop flags;
- completion time; and
- a short, non-identifying observation.

The redesign evidence contains `baseline`, `redesign`, and a `design_changes` list. Evaluate files offline with:

```bash
python3 scripts/evaluate_trials.py baseline runtime/baseline.json --output runtime/baseline_checked.json
python3 scripts/evaluate_trials.py redesign runtime/comparison.json --output runtime/comparison_checked.json
```

Passing requires five matched scenarios, no safety stops, no access barriers in the retest, no task-success regression, and improvement in at least two target metrics. This is a design gate, not proof of general usability; the same participant may perform better from learning alone.

## Submission

Submit `student_submission/` and the individual Git commit. Include raw/checked JSON, ROS event traces, baseline and redesign configuration, state diagrams/screenshots, explanations, final synthesis, and `manifest.json`. Inspect the commit once more for identifying data before pushing.

## Maintainer checks

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

ROS integration additionally requires `colcon build --symlink-install` under Jazzy.
