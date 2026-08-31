from __future__ import annotations

from typing import Any

from lab.models import RequirementResult, make_check
from simulation.kinematics import SEQUENCES, integrate_sequence


REFLECTIONS = ("model_vs_observation", "largest_error", "error_source", "twice_distance")


def evaluate(runs: list[dict[str, Any]], responses: dict[str, Any]):
    predictions = responses.get("mission_1.predictions", {})
    locked_at = str(responses.get("mission_1.predictions_locked_at", ""))
    expected = {name: integrate_sequence(segments) for name, segments in SEQUENCES.items()}
    prediction_correct = 0
    for name, pose in expected.items():
        submitted = predictions.get(name, {})
        try:
            good = (
                abs(float(submitted.get("x")) - pose["x"]) <= 0.06
                and abs(float(submitted.get("y")) - pose["y"]) <= 0.06
                and abs(float(submitted.get("theta")) - pose["theta"]) <= 0.12
            )
        except (TypeError, ValueError):
            good = False
        prediction_correct += good
    by_name = {str(run.get("sequence_id")): run for run in runs}
    completed = sum(bool(by_name.get(name, {}).get("completed")) and bool(by_name.get(name, {}).get("stop_sent")) for name in SEQUENCES)
    chronological = bool(locked_at) and all(str(by_name.get(name, {}).get("captured_at", "")) >= locked_at for name in SEQUENCES)
    error_metrics = sum(
        all(key in by_name.get(name, {}) for key in ("position_error", "heading_error"))
        for name in SEQUENCES
    )
    reflections = all(str(responses.get(f"mission_1.{key}", "")).strip() for key in REFLECTIONS)
    requirements = [
        RequirementResult("predictions", "Final-pose predictions are numerically correct", prediction_correct == 3, prediction_correct, "3/3 within tolerance"),
        RequirementResult("locked", "Predictions locked before execution", chronological, locked_at or "not locked", "before all runs"),
        RequirementResult("runs", "Three sequences completed with safe stops", completed == 3, completed, "3/3"),
        RequirementResult("errors", "Pose discrepancies calculated", error_metrics == 3, error_metrics, "3/3"),
        RequirementResult("reflection", "Motion-model analysis completed", reflections, "complete" if reflections else "incomplete", "complete"),
    ]
    return make_check("You predicted motion and compared the model with observed robot pose.", requirements)

