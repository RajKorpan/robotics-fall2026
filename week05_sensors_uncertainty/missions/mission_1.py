from __future__ import annotations

from lab.models import RequirementResult, make_check

REFLECTIONS = ("bias_vs_variance", "more_samples", "robot_consequence")


def _close(answer, actual, tolerance):
    try:
        return abs(float(answer) - float(actual)) <= tolerance
    except (TypeError, ValueError):
        return False


def evaluate(metrics: dict, profile_name: str, responses: dict):
    requirements = [
        RequirementResult("mean", "Mean estimated", _close(responses.get("mission_1.mean"), metrics["mean"], 0.03), responses.get("mission_1.mean", ""), "within 0.03 m"),
        RequirementResult("variance", "Sample variance estimated", _close(responses.get("mission_1.variance"), metrics["variance"], max(0.004, metrics["variance"] * 0.18)), responses.get("mission_1.variance", ""), "within 18% (or 0.004 m²)"),
        RequirementResult("bias", "Bias estimated", _close(responses.get("mission_1.bias"), metrics["bias"], 0.03), responses.get("mission_1.bias", ""), "within 0.03 m"),
        RequirementResult("median", "Median estimated", _close(responses.get("mission_1.median"), metrics["median"], 0.03), responses.get("mission_1.median", ""), "within 0.03 m"),
        RequirementResult("dropouts", "Dropouts counted", _close(responses.get("mission_1.dropouts"), metrics["dropout_count"], 0), responses.get("mission_1.dropouts", ""), str(metrics["dropout_count"])),
        RequirementResult("outliers", "Outliers counted", _close(responses.get("mission_1.outliers"), metrics["outlier_count"], 0), responses.get("mission_1.outliers", ""), str(metrics["outlier_count"])),
        RequirementResult("diagnosis", "Dominant imperfection diagnosed", responses.get("mission_1.profile") == profile_name, responses.get("mission_1.profile", ""), "supported profile"),
    ]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_1.{key}", "")).strip()
        requirements.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 80, len(text), "at least 80 characters"))
    return make_check("Mission 1 evidence is complete and internally consistent.", requirements)
