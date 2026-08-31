from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str; title: str; stages: tuple[str, ...]; missions: tuple[str, ...]
    submission_directory: str = "student_submission"


LAB = LabConfig("week11_hri_evaluation", "Week 11: Human–Robot Interaction Evaluation", ("intro", "concepts", "preflight", "mission_1", "mission_2", "mission_3", "final"), ("mission_1", "mission_2", "mission_3"))

