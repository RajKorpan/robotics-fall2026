from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    subtitle: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    evidence_directory: str = "runtime/evidence"
    submission_directory: str = "student_submission"
    instructor_password_env: str = "WEEK03_INSTRUCTOR_PASSWORD"


LAB = LabConfig(
    id="week03_motion_frames_ai",
    title="Week 3: Motion, Frames, and AI-Assisted ROS Development",
    subtitle="Predict motion, reason across frames, and verify AI-assisted code",
    stages=("intro", "concepts", "preflight", "mission_1", "mission_2", "mission_3", "final"),
    missions=("mission_1", "mission_2", "mission_3"),
)

