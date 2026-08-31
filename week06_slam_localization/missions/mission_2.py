from lab.models import RequirementResult, make_check
REFLECTIONS = ("strategy_prediction", "comparison", "loop_closure")
def evaluate(first, second, responses):
    m1 = (first or {}).get("metrics", {}); m2 = (second or {}).get("metrics", {})
    strategies = {(first or {}).get("strategy"), (second or {}).get("strategy")}
    req = [
        RequirementResult("runs", "Two valid analyzed maps", bool(m1) and bool(m2), len([x for x in (m1, m2) if x]), "2"),
        RequirementResult("strategies", "Different exploration strategies", len(strategies - {None, ""}) == 2, sorted(x for x in strategies if x), "2 different strategies"),
        RequirementResult("coverage", "Both maps have useful coverage", min(m1.get("known_fraction", 0), m2.get("known_fraction", 0)) >= .15, round(min(m1.get("known_fraction", 0), m2.get("known_fraction", 0)), 3), "≥ 0.15 each"),
    ]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_2.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "≥ 120 characters"))
    return make_check("Mission 2 compares two mapping strategies using matched evidence.", req)
