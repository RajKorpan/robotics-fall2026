from dataclasses import dataclass


@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"


LAB = LabConfig(
    id="week09_planning_navigation",
    title="Week 9: Planning and Human-Aware Navigation",
    stages=("intro", "concepts", "preflight", "mission_1", "mission_2", "mission_3", "final"),
    missions=("mission_1", "mission_2", "mission_3"),
)

