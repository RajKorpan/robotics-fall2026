from lab.models import RequirementResult, make_check
REFLECTIONS = ("system_trace", "breakdown", "fallback")
def evaluate(evidence, responses, screenshot_count):
    result = (evidence or {}).get("result", {}); rows = result.get("rows", [])
    req = [RequirementResult("scenarios", "Seven behavior scenarios executed", result.get("scenario_count", 0) >= 7, result.get("scenario_count", 0), "≥ 7"), RequirementResult("behavior", "Expected states produced", result.get("passed_count", 0) == result.get("scenario_count", -1), f"{result.get('passed_count', 0)}/{result.get('scenario_count', 0)}", "all"), RequirementResult("safety", "Safety invariants pass", bool(result.get("safety_invariants_passed")), result.get("safety_invariants_passed", False), "true"), RequirementResult("screens", "ROS behavior evidence supplied", screenshot_count >= 2, screenshot_count, "≥ 2")]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_3.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "≥ 120 characters"))
    return make_check("Mission 3 connects uncertain perception to bounded robot action.", req)
