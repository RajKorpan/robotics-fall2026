# robotics-fall2026

Interactive teaching labs for CSCI 39536: Introduction to Robotics.

## Shared ROS 2 environment

Weeks 1, 3, 6, 8, 9, and 11 reuse one cross-platform Docker environment. Students install and build it once during Week 1, then select the active lab with a course launcher. See [ROS_DOCKER_SETUP.md](ROS_DOCKER_SETUP.md).

## Projects

- `week01_ros_foundations/` — individual ROS 2 lab for inspecting, controlling, and extending a simulated mobile robot.
- `week03_motion_frames_ai/` — individual ROS 2 lab for motion prediction, TF reasoning, and verified AI-assisted development.
- `week04_pid_odometry/` — individual, self-contained lab for PID control and odometry.
- `week05_sensors_uncertainty/` — individual, self-contained lab for sensor characterization, filtering, fusion, and decisions under uncertainty.
- `week06_slam_localization/` — individual ROS 2 lab for mapping, exploration-strategy comparison, and localization under difficult conditions.
- `week08_vision_perception/` — individual ROS 2 lab comparing classical and learned vision and connecting perception to bounded behavior.
- `week09_planning_navigation/` — individual ROS 2 lab for path inspection, repeatable Nav2 trials, and a human-aware navigation redesign.
- `week10_foundation_models/` — individual, self-contained lab for evaluating foundation-model plans and visual interpretations through a safety verification layer.
- `week11_hri_evaluation/` — individual ROS 2 lab using paired participation for baseline interaction evaluation, evidence-driven redesign, and matched retesting.
- `week12_responsible_robotics/` — individual, self-contained lab translating privacy, fairness, safety, accessibility, and human-control requirements into tested system behavior.
- `week14_pendulum_rl/` — individual, self-contained lab for reinforcement-learning using a pendulum.
- `lab-template/` — reusable architecture for additional labs.

Each project has its own README, dependencies, run instructions, and submission format.
