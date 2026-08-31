from __future__ import annotations

from typing import Any

from lab.models import RequirementResult, make_check


RELATIONSHIPS = {
    "odom_to_base": "odom → base_link",
    "base_to_sensor": "base_link → base_scan",
    "map_role": "Global frame corrected by localization or SLAM",
}
DIAGNOSTICS = {"typo": "Unknown frame name", "wrong_source": "Point interpreted in the wrong source frame", "stale": "Transform unavailable at the requested time"}
REFLECTIONS = ("fixed_meaning", "moving_coordinates", "sensor_offset", "map_absent")


def evaluate(snapshot: dict[str, Any], responses: dict[str, Any]):
    frames = set(snapshot.get("frames", []))
    required_frames = {"odom", "base_link", "base_scan"}
    relationships = responses.get("mission_2.relationships", {})
    relationship_count = sum(relationships.get(key) == value for key, value in RELATIONSHIPS.items())
    diagnostics = responses.get("mission_2.diagnostics", {})
    diagnostic_count = sum(diagnostics.get(key) == value for key, value in DIAGNOSTICS.items())
    point_answers = responses.get("mission_2.point_answers", {})
    transformed = snapshot.get("transformed_points", {})
    point_count = 0
    for key, actual in transformed.items():
        answer = point_answers.get(key, {})
        try:
            point_count += abs(float(answer.get("x")) - float(actual["x"])) <= 0.08 and abs(float(answer.get("y")) - float(actual["y"])) <= 0.08
        except (TypeError, ValueError, KeyError):
            pass
    reflections = all(str(responses.get(f"mission_2.{key}", "")).strip() for key in REFLECTIONS)
    requirements = [
        RequirementResult("snapshot", "Live TF snapshot captured", bool(snapshot.get("captured_at")), snapshot.get("captured_at", "missing"), "timestamp present"),
        RequirementResult("frames", "Required frames observed", required_frames.issubset(frames), sorted(frames), sorted(required_frames)),
        RequirementResult("relationships", "Frame relationships interpreted", relationship_count == 3, relationship_count, "3/3"),
        RequirementResult("points", "Two point transforms calculated", point_count >= 2, point_count, ">= 2 within tolerance"),
        RequirementResult("diagnostics", "Injected frame problems diagnosed", diagnostic_count == 3, diagnostic_count, "3/3"),
        RequirementResult("reflection", "Frame reasoning completed", reflections, "complete" if reflections else "incomplete", "complete"),
    ]
    return make_check("You interpreted robot, odometry, and sensor coordinates correctly.", requirements)

