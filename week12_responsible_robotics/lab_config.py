from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str; title: str; stages: tuple[str, ...]; missions: tuple[str, ...]
    submission_directory: str = "student_submission"


LAB = LabConfig("week12_responsible_robotics", "Week 12: Responsible Robotics by Design", ("intro","concepts","background","playground","lab","final_submission"), ("mission_1","mission_2","mission_3"))

