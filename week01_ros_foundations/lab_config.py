from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    subtitle: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"
    evidence_directory: str = "runtime/evidence"
    instructor_password_env: str = "WEEK01_INSTRUCTOR_PASSWORD"


LAB = LabConfig(
    id="week01_ros_foundations",
    title="Week 1: Discovering a Robot Through ROS 2",
    subtitle="Observe, control, and extend a simulated mobile robot",
    stages=("intro", "concepts", "preflight", "mission_1", "mission_2", "mission_3", "final"),
    missions=("mission_1", "mission_2", "mission_3"),
)

