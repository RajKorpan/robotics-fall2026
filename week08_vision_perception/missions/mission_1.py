from evaluation.metrics import conditions_complete
from lab.models import RequirementResult, make_check
REFLECTIONS = ("prediction", "parameter_effect", "failure_analysis")
def evaluate(evidence, responses, screenshot_count):
    metrics = (evidence or {}).get("metrics", {}); rows = (evidence or {}).get("rows", [])
    req = [RequirementResult("conditions", "All assigned conditions tested", conditions_complete(rows), metrics.get("conditions", []), "8 conditions"), RequirementResult("precision", "Classical precision", metrics.get("precision", 0) >= .65, round(metrics.get("precision", 0), 3), "≥ 0.65"), RequirementResult("recall", "Classical recall", metrics.get("recall", 0) >= .65, round(metrics.get("recall", 0), 3), "≥ 0.65"), RequirementResult("screens", "Masks/annotations supplied", screenshot_count >= 4, screenshot_count, "≥ 4 images")]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_1.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 110, len(text), "≥ 110 characters"))
    return make_check("Mission 1 documents a tested classical perception pipeline.", req)
