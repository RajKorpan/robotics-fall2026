from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    linear_x: float
    angular_z: float
    duration: float


SEQUENCES = {
    "straight": (Segment(0.15, 0.0, 3.0),),
    "turn_then_drive": (Segment(0.0, 0.5, math.pi), Segment(0.15, 0.0, 2.0)),
    "arc": (Segment(0.15, 0.4, 4.0),),
}


def integrate_segment(x: float, y: float, theta: float, segment: Segment) -> tuple[float, float, float]:
    v, omega, duration = segment.linear_x, segment.angular_z, segment.duration
    if abs(omega) < 1e-9:
        return x + v * duration * math.cos(theta), y + v * duration * math.sin(theta), theta
    final_theta = theta + omega * duration
    radius = v / omega
    return (
        x + radius * (math.sin(final_theta) - math.sin(theta)),
        y - radius * (math.cos(final_theta) - math.cos(theta)),
        math.atan2(math.sin(final_theta), math.cos(final_theta)),
    )


def integrate_sequence(segments: tuple[Segment, ...], initial=(0.0, 0.0, 0.0)) -> dict[str, float]:
    x, y, theta = initial
    for segment in segments:
        x, y, theta = integrate_segment(x, y, theta, segment)
    return {"x": x, "y": y, "theta": theta}


def pose_error(predicted: dict[str, float], observed: dict[str, float]) -> dict[str, float]:
    return {
        "position_error": math.hypot(observed["x"] - predicted["x"], observed["y"] - predicted["y"]),
        "heading_error": abs(math.atan2(math.sin(observed["theta"] - predicted["theta"]), math.cos(observed["theta"] - predicted["theta"]))),
    }

