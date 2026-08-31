from evaluation.metrics import conditions_complete
from lab.models import RequirementResult, make_check
REFLECTIONS = ("threshold_tradeoff", "comparison", "confidence_limit")
def evaluate(evidence, responses, screenshot_count):
    metrics = (evidence or {}).get("metrics", {}); rows = (evidence or {}).get("rows", []); sweep = (evidence or {}).get("threshold_sweep", [])
    req = [RequirementResult("conditions", "All assigned conditions tested", conditions_complete(rows), metrics.get("conditions", []), "8 conditions"), RequirementResult("sweep", "Confidence sweep completed", len(sweep) >= 5, len(sweep), "≥ 5 thresholds"), RequirementResult("threshold", "Operating threshold selected", .20 <= float((evidence or {}).get("selected_threshold", -1)) <= .90, (evidence or {}).get("selected_threshold", "missing"), "0.20–0.90"), RequirementResult("screens", "Success/failure detections supplied", screenshot_count >= 4, screenshot_count, "≥ 4 images")]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_2.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "≥ 120 characters"))
    return make_check("Mission 2 includes a calibrated learned-perception evaluation.", req)
