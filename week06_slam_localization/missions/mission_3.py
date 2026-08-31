from analysis.localization import trial_passes
from lab.models import RequirementResult, make_check
CONDITIONS = ("good_initial_pose", "incorrect_initial_pose", "ambiguous_location", "degraded_sensor")
REFLECTIONS = ("knowing_where", "recovery", "sensor_effect", "deployment_limit")
def evaluate(trials, responses):
    req = []
    for condition in CONDITIONS:
        evidence = trials.get(condition, {}); metrics = evidence.get("metrics", {})
        req.append(RequirementResult(condition, condition.replace("_", " ").title(), trial_passes(condition, metrics), metrics or "missing", "condition criteria"))
    good = trials.get("good_initial_pose", {}).get("metrics", {}); degraded = trials.get("degraded_sensor", {}).get("metrics", {})
    comparison = good.get("final_covariance") is not None and degraded.get("final_covariance") is not None and degraded.get("scan_retention", 1) <= .60
    req.append(RequirementResult("degradation", "Normal/degraded comparison is measurable", comparison, f"good covariance={good.get('final_covariance')}, degraded covariance={degraded.get('final_covariance')}, retention={degraded.get('scan_retention')}", "both uncertainties plus ≤60% retention"))
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_3.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 120, len(text), "≥ 120 characters"))
    return make_check("Mission 3 documents localization success, failure, recovery, and limits.", req)
