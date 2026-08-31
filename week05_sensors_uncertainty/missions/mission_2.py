from __future__ import annotations

from lab.models import RequirementResult, make_check

REFLECTIONS = ("comparison", "responsiveness", "fusion_choice")
LIMITS = {"rmse": 0.18, "max_error": 1.85, "response_delay": 1.25, "availability": 0.99}


def evaluate(attempts: list[dict], selected_index: int, responses: dict):
    methods = {item.get("settings", {}).get("method") for item in attempts}
    selected = attempts[selected_index] if attempts and 0 <= selected_index < len(attempts) else {}
    metrics = selected.get("metrics", {})
    requirements = [
        RequirementResult("attempts", "At least three configurations tested", len(attempts) >= 3, len(attempts), "3 or more"),
        RequirementResult("methods", "Moving average and median compared", {"Moving average", "Median"}.issubset(methods), sorted(x for x in methods if x), "both required methods"),
        RequirementResult("rmse", "Selected RMSE", metrics.get("rmse", 99) <= LIMITS["rmse"], round(metrics.get("rmse", 99), 3), f"≤ {LIMITS['rmse']} m"),
        RequirementResult("maximum", "Selected maximum error", metrics.get("max_error", 99) <= LIMITS["max_error"], round(metrics.get("max_error", 99), 3), f"≤ {LIMITS['max_error']} m"),
        RequirementResult("delay", "Selected response delay", metrics.get("response_delay", 99) <= LIMITS["response_delay"], metrics.get("response_delay", 99), f"≤ {LIMITS['response_delay']} s"),
        RequirementResult("availability", "Selected estimate availability", metrics.get("availability", 0) >= LIMITS["availability"], metrics.get("availability", 0), f"≥ {LIMITS['availability']:.0%}"),
    ]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_2.{key}", "")).strip()
        requirements.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 100, len(text), "at least 100 characters"))
    return make_check("Mission 2 includes a tested, defensible filtering and fusion design.", requirements)
