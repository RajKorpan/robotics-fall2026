from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"


LAB = LabConfig(
    id="week10_foundation_models",
    title="Lab 9: Foundation Models for Robotics",
    stages=("intro", "preflight", "guided", "mission_1", "mission_2", "mission_3", "final_submission"),
    missions=("mission_1", "mission_2", "mission_3"),
)

