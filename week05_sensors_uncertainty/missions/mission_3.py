from __future__ import annotations

from lab.models import RequirementResult, make_check

REFLECTIONS = ("error_costs", "context_comparison", "limitations")


def evaluate(results: dict, responses: dict):
    requirements = []
    for context in ("Warehouse", "Assistive"):
        result = results.get(context, {})
        requirements.append(RequirementResult(context.lower(), f"{context} policy passes", bool(result.get("passed")), result.get("metrics", "not tested"), "all context criteria"))
    warehouse = results.get("Warehouse", {}).get("settings", {})
    assistive = results.get("Assistive", {}).get("settings", {})
    differences = sum(warehouse.get(key) != assistive.get(key) for key in set(warehouse) | set(assistive)) if warehouse and assistive else 0
    requirements.append(RequirementResult("context_specific", "Policies are context-specific", differences >= 2, differences, "at least 2 parameter differences"))
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_3.{key}", "")).strip()
        requirements.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "at least 120 characters"))
    return make_check("Mission 3 demonstrates context-sensitive decisions under uncertainty.", requirements)
