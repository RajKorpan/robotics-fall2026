from lab.models import MissionCheck, MissionDefinition, ReflectionPrompt, RequirementResult
from simulation.vision import run_vision_suite


def render_controls(st):
    return {"confidence_threshold": st.slider("Accept model output at confidence ≥", .30, .95, .65, .05)}
def evaluate(result):
    m = result.metrics; abstained = m["scenes_tested"] - m["accepted_detections"]; requirements = [
        RequirementResult("coverage", "All visual conditions evaluated", m["scenes_tested"] == 8, m["scenes_tested"], "8"),
        RequirementResult("errors", "False interpretations visible", m["errors_observed"] >= 4, m["errors_observed"], ">= 4"),
        RequirementResult("unsafe_accept", "At least one confident unsafe recommendation exposed", m["unsafe_recommendations_accepted"] >= 1, m["unsafe_recommendations_accepted"], ">= 1"),
        RequirementResult("abstention", "Threshold causes at least one abstention", abstained >= 1, abstained, ">= 1"),
    ]; return MissionCheck(all(r.passed for r in requirements), "The scene suite exposes the limits of confidence as a reliability signal.", requirements)
MISSION = MissionDefinition("mission_2", "Mission 2 — Vision, language, and confidence", "Systematically vary visual conditions and test whether confidence separates correct, incorrect, safe, and unsafe recommendations.", render_controls, run_vision_suite, evaluate, (
    ReflectionPrompt("condition_failures", "Compare occlusion, ambiguity, unusual objects, and misleading context. What visual assumption failed in each?"),
    ReflectionPrompt("confidence", "Use the measured confidence values to explain why confidence is not a correctness guarantee."),
    ReflectionPrompt("threshold_tradeoff", "Defend your chosen threshold. Which useful outputs were withheld and which unsafe outputs remained?"),
))

