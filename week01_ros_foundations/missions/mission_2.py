from __future__ import annotations

from typing import Any

from lab.models import RequirementResult, check_from_requirements


TRIAL_TYPES = ("straight", "rotation", "curve")
REFLECTION_KEYS = (
    "velocity_vs_destination",
    "combined_velocity",
    "least_accurate",
    "command_vs_motion",
    "safe_stop",
    "timing_evidence",
    "delay_risk",
    "stale_command",
)


def evaluate(trials: list[dict[str, Any]], responses: dict[str, Any]):
    by_type = {str(trial.get("trial_type")): trial for trial in trials}
    predictions = responses.get("mission_2.predictions", {})
    prediction_names = (*TRIAL_TYPES, "curve_modified")
    prediction_count = sum(bool(str(predictions.get(name, "")).strip()) for name in prediction_names)
    locked_at = str(responses.get("mission_2.predictions_locked_at", ""))
    predictions_precede_trials = bool(locked_at) and all(
        str(trial.get("captured_at", "")) >= locked_at for trial in trials
    ) if trials else False
    complete_trials = sum(
        name in by_type
        and bool(by_type[name].get("completed"))
        and bool(by_type[name].get("stop_sent"))
        for name in TRIAL_TYPES
    )
    safe_commands = all(
        abs(float(trial.get("linear_x", 0.0))) <= 0.22
        and abs(float(trial.get("angular_z", 0.0))) <= 0.8
        for trial in trials
    ) if trials else False
    modified_curve = any(str(trial.get("trial_type")) == "curve_modified" and trial.get("completed") for trial in trials)
    timing_trials = sum(
        name in by_type
        and by_type[name].get("command_started_at")
        and by_type[name].get("zero_command_sent_at")
        and by_type[name].get("actual_command_duration") is not None
        and by_type[name].get("duration_error") is not None
        for name in prediction_names
    )
    target_complete = bool(responses.get("mission_2.target_reached"))
    command_path = str(responses.get("mission_2.command_path", "")).strip()
    reflections_complete = all(str(responses.get(f"mission_2.{key}", "")).strip() for key in REFLECTION_KEYS)
    requirements = [
        RequirementResult("predictions", "Predictions recorded and locked", prediction_count == 4 and bool(locked_at), prediction_count, "4/4 and timestamped"),
        RequirementResult("prediction_order", "Predictions precede recorded trials", predictions_precede_trials, locked_at or "not locked", "locked before every trial"),
        RequirementResult("trials", "Straight, rotation, and curve trials completed", complete_trials == 3, complete_trials, "3/3 with stop"),
        RequirementResult("limits", "Recorded commands remain within course limits", safe_commands, "within limits" if safe_commands else "missing/out of range", "|linear| <= 0.22, |angular| <= 0.8"),
        RequirementResult("modified_curve", "Modified curve trial completed", modified_curve, modified_curve, "true"),
        RequirementResult("timing", "Command timing recorded for all four trials", timing_trials == 4, timing_trials, "4/4"),
        RequirementResult("target", "Target-zone challenge completed", target_complete, target_complete, "true"),
        RequirementResult("path", "Command path explained", len(command_path) >= 80, len(command_path), ">= 80 characters"),
        RequirementResult("reflections", "Mission reflections completed", reflections_complete, "complete" if reflections_complete else "incomplete", "complete"),
    ]
    return check_from_requirements("You connected velocity commands to observed robot motion.", requirements)
