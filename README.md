# robotics-fall2026

Interactive teaching labs for CSCI 39536: Introduction to Robotics.

## Shared ROS 2 environment

Weeks 1, 3, 6, 8, 9, and 11 reuse one cross-platform Docker environment. Students install and build it once during Week 1, then select the active lab with a course launcher. See [ROS_DOCKER_SETUP.md](ROS_DOCKER_SETUP.md).

## Projects

- [Week 1 overview](week01_ros_foundations/OVERVIEW.md) — individual ROS 2 lab for inspecting, controlling, and extending a simulated mobile robot.
- [Week 3 overview](week03_motion_frames_ai/OVERVIEW.md) — individual ROS 2 lab for motion prediction, TF reasoning, and verified AI-assisted development.
- [Week 4 overview](week04_pid_odometry/OVERVIEW.md) — individual, self-contained lab for PID control and odometry.
- [Week 5 overview](week05_sensors_uncertainty/OVERVIEW.md) — individual, self-contained lab for sensor characterization, filtering, fusion, and decisions under uncertainty.
- [Week 6 overview](week06_slam_localization/OVERVIEW.md) — individual ROS 2 lab for mapping, exploration-strategy comparison, and localization under difficult conditions.
- [Week 8 overview](week08_vision_perception/OVERVIEW.md) — individual ROS 2 lab comparing classical and learned vision and connecting perception to bounded behavior.
- [Week 9 overview](week09_planning_navigation/OVERVIEW.md) — individual ROS 2 lab for path inspection, repeatable Nav2 trials, and a human-aware navigation redesign.
- [Week 10 overview](week10_foundation_models/OVERVIEW.md) — individual, self-contained lab for evaluating foundation-model plans and visual interpretations through a safety verification layer.
- [Week 11 overview](week11_hri_evaluation/OVERVIEW.md) — individual ROS 2 lab using paired participation for baseline interaction evaluation, evidence-driven redesign, and matched retesting.
- [Week 12 overview](week12_responsible_robotics/OVERVIEW.md) — individual, self-contained lab translating privacy, fairness, safety, accessibility, and human-control requirements into tested system behavior.
- [Week 14 overview](week14_pendulum_rl/OVERVIEW.md) — individual, self-contained lab for reinforcement-learning using a pendulum.
- `lab-template/` — reusable architecture for additional labs.

Each project has its own README, dependencies, run instructions, and submission format.
