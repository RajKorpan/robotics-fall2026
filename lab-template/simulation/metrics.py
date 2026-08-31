from __future__ import annotations


def feedback_metrics(trace: dict[str, list[float]]) -> dict[str, float]:
    target = trace["target"][-1]
    position = trace["position"]
    errors = [abs(value) for value in trace["error"]]
    overshoot = max(0.0, max(position) - target)
    final_error = errors[-1]
    mean_error = sum(errors) / len(errors)
    return {
        "final_error": final_error,
        "mean_absolute_error": mean_error,
        "overshoot": overshoot,
    }

