from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LabConfig:
    id: str
    title: str
    subtitle: str
    stages: tuple[str,...]
    missions: tuple[str,...]
    submission_directory: str="student_submission"
    instructor_password_env: str="WEEK05_INSTRUCTOR_PASSWORD"

LAB=LabConfig(
    id="week05_sensors_uncertainty",
    title="Week 5: Sensors, Noise, and Uncertainty",
    subtitle="Characterize measurements, filter and fuse sensors, and make defensible decisions",
    stages=("intro","concepts","mission_1","mission_2","mission_3","final"),
    missions=("mission_1","mission_2","mission_3"),
)

