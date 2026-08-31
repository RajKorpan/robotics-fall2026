from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    subtitle: str
    submission_directory: str
    instructor_password_env: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]


LAB = LabConfig(
    id="feedback_systems_template",
    title="Robotics Lab Template",
    subtitle="A reusable scaffold for interactive, evidence-based robotics labs",
    submission_directory="student_submission",
    instructor_password_env="LAB_INSTRUCTOR_PASSWORD",
    stages=("intro", "concepts", "background", "playground", "lab", "final_submission"),
    missions=("mission_1", "mission_2", "mission_3"),
)

