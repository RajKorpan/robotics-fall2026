from dataclasses import dataclass

@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"

LAB = LabConfig(
    id="week06_slam_localization",
    title="Week 6: SLAM and Localization",
    stages=("intro", "concepts", "preflight", "mission_1", "mission_2", "mission_3", "final"),
    missions=("mission_1", "mission_2", "mission_3"),
)
