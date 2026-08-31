from __future__ import annotations

from lab.models import MissionCheck, MissionDefinition, ReflectionPrompt, RequirementResult
from missions.common import run_feedback_mission


def render_controls(st) -> dict:
    return {
        "gain": st.slider("Controller gain", 0.1, 4.0, 1.5, 0.1),
        "target": 1.0,
        "disturbance": -0.35,
        "sensor_noise": 0.0,
    }


def run(settings: dict):
    return run_feedback_mission("mission_2", settings)


def evaluate(result) -> MissionCheck:
    final_error = float(result.metrics["final_error"])
    overshoot = float(result.metrics["overshoot"])
    requirements = [
        RequirementResult("final_error", "Final error", final_error < 0.20, final_error, "< 0.20"),
        RequirementResult("overshoot", "Overshoot", overshoot < 0.35, overshoot, "< 0.35"),
    ]
    return MissionCheck(all(item.passed for item in requirements), "Reject a persistent disturbance.", requirements)


MISSION = MissionDefinition(
    id="mission_2",
    title="Mission 2 — Handle a disturbance",
    objective="Retune the controller after an external force is introduced.",
    render_controls=render_controls,
    run=run,
    evaluate=evaluate,
    reflection_prompts=(ReflectionPrompt("m2_tradeoff", "Describe the accuracy-versus-overshoot trade-off you observed."),),
)

