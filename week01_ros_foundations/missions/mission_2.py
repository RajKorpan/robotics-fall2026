from __future__ import annotations

from typing import Any

from lab.models import RequirementResult, check_from_requirements


TRIAL_TYPES = ("straight", "rotation", "curve", "curve_modified")
SYNTHESIS_KEYS = ("motion_comparison", "measurement_explanation", "safety_explanation")


def mission_responses(responses: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in responses.items()
        if key.startswith("mission_2.")
    }


def motion_observed(name: str, trial: dict[str, Any]) -> bool:
    displacement = abs(float(trial.get("displacement", 0.0)))
    path_length = abs(float(trial.get("observed_path_length", displacement)))
    heading_change = abs(float(trial.get("heading_change", 0.0)))
    if name == "rotation":
        return heading_change >= 0.3
    if name in ("curve", "curve_modified"):
        return path_length >= 0.05 and heading_change >= 0.2
    return path_length >= 0.05


def evaluate(trials: list[dict[str, Any]], responses: dict[str, Any]):
    by_type = {str(trial.get("trial_type")): trial for trial in trials if trial.get("trial_type") in TRIAL_TYPES}
    predictions = responses.get("mission_2.predictions", {})
    locks = responses.get("mission_2.prediction_locks", {})

    prediction_count = sum(len(str(predictions.get(name, "")).strip()) >= 30 for name in TRIAL_TYPES)
    locked_count = sum(bool(locks.get(name)) for name in TRIAL_TYPES)
    completed_count = sum(
        bool(by_type.get(name, {}).get("completed")) and bool(by_type.get(name, {}).get("stop_sent"))
        for name in TRIAL_TYPES
    )
    motion_count = sum(motion_observed(name, by_type.get(name, {})) for name in TRIAL_TYPES)
    ordered_count = sum(
        bool(locks.get(name))
        and str(by_type.get(name, {}).get("captured_at", "")) >= str(locks.get(name, ""))
        for name in TRIAL_TYPES
    )
    timing_count = sum(
        bool(
            by_type.get(name, {}).get("actual_command_duration") is not None
            and by_type.get(name, {}).get("duration_error") is not None
            and by_type.get(name, {}).get("zero_command_sent_at")
        )
        for name in TRIAL_TYPES
    )
    safe_commands = len(by_type) == len(TRIAL_TYPES) and all(
        abs(float(trial.get("linear_x", 0.0))) <= 0.22
        and abs(float(trial.get("angular_z", 0.0))) <= 0.8
        for trial in by_type.values()
    )

    modified_settings = responses.get("mission_2.modified_settings", {})
    modified_trial = by_type.get("curve_modified", {})
    modified_matches = bool(modified_trial) and all(
        abs(float(modified_trial.get(field, 999.0)) - float(modified_settings.get(field, -999.0))) < 1e-6
        for field in ("linear_x", "angular_z", "duration")
    )
    synthesis_count = sum(
        len(str(responses.get(f"mission_2.{key}", "")).strip()) >= 60
        for key in SYNTHESIS_KEYS
    )

    requirements = [
        RequirementResult("predictions", "Four predictions were written before running", prediction_count == 4 and locked_count == 4, f"{prediction_count} written, {locked_count} saved", "4 written and saved"),
        RequirementResult("trials", "Four motion trials completed with a stop command", completed_count == 4, completed_count, "4 of 4"),
        RequirementResult("motion", "Each trial produced the expected kind of measurable motion", motion_count == 4, motion_count, "4 of 4"),
        RequirementResult("prediction_order", "Each saved prediction came before its trial", ordered_count == 4, ordered_count, "4 of 4"),
        RequirementResult("limits", "All commands stayed within the course speed limits", safe_commands, "within limits" if safe_commands else "missing or outside limits", "within limits"),
        RequirementResult("modified_settings", "The recorded modified curve matches the selected sliders", modified_matches, "matches" if modified_matches else "run again after changing sliders", "matches"),
        RequirementResult("timing", "Timing and zero-command evidence were recorded", timing_count == 4, timing_count, "4 of 4"),
        RequirementResult("synthesis", "Three evidence-based explanations are complete", synthesis_count == 3, synthesis_count, "3 of 3"),
    ]
    return check_from_requirements("You connected velocity commands to measured robot motion.", requirements)
