from lab.models import RequirementResult, make_check
REFLECTIONS = ("system_observation", "map_interpretation", "limitations")
def evaluate(evidence, responses, has_yaml, has_image):
    metrics = (evidence or {}).get("metrics", {})
    req = [
        RequirementResult("files", "Map YAML and image supplied", has_yaml and has_image, f"YAML={has_yaml}, image={has_image}", "both files"),
        RequirementResult("coverage", "Known map coverage", metrics.get("known_fraction", 0) >= .15, round(metrics.get("known_fraction", 0), 3), "≥ 0.15"),
        RequirementResult("resolution", "Valid resolution", 0 < metrics.get("resolution", 0) <= .10, metrics.get("resolution", "missing"), "0–0.10 m/cell"),
        RequirementResult("quality", "Map quality score", (evidence or {}).get("quality_score", 0) >= 45, (evidence or {}).get("quality_score", 0), "≥ 45"),
    ]
    for key in REFLECTIONS:
        text = str(responses.get(f"mission_1.{key}", "")).strip(); req.append(RequirementResult(key, key.replace("_", " ").title(), len(text) >= 100, len(text), "≥ 100 characters"))
    return make_check("Mission 1 includes a usable map and an evidence-based explanation.", req)
