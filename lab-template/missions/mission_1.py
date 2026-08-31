from __future__ import annotations

from lab.models import MissionCheck, MissionDefinition, ReflectionPrompt, RequirementResult
from missions.common import run_feedback_mission


def render_controls(st) -> dict:
    return {
        "gain": st.slider("Controller gain", 0.1, 4.0, 1.0, 0.1),
        "target": 1.0,
        "disturbance": 0.0,
        "sensor_noise": 0.0,
    }


def run(settings: dict):
    return run_feedback_mission("mission_1", settings)


def evaluate(result) -> MissionCheck:
    value = float(result.metrics["final_error"])
    requirement = RequirementResult("final_error", "Final error", value < 0.08, value, "< 0.08")
    return MissionCheck(requirement.passed, "Reach the target using feedback.", [requirement])


MISSION = MissionDefinition(
    id="mission_1",
    title="Mission 1 — Establish feedback",
    objective="Tune one gain so the system reaches its target accurately.",
    render_controls=render_controls,
    run=run,
    evaluate=evaluate,
    reflection_prompts=(ReflectionPrompt("m1_explain", "Explain how changing the gain changed the response."),),
)

