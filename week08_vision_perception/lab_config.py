from dataclasses import dataclass

@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    stages: tuple[str, ...]
    missions: tuple[str, ...]
    submission_directory: str = "student_submission"

LAB = LabConfig(
    id="week08_vision_perception",
    title="Week 8: Computer Vision and Learned Perception",
    stages=("intro", "concepts", "preflight", "mission_1", "mission_2", "mission_3", "final"),
    missions=("mission_1", "mission_2", "mission_3"),
)
