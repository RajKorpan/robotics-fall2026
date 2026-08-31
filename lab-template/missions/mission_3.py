from __future__ import annotations

from lab.models import MissionCheck, MissionDefinition, ReflectionPrompt, RequirementResult
from missions.common import run_feedback_mission


def render_controls(st) -> dict:
    return {
        "gain": st.slider("Controller gain", 0.1, 4.0, 1.5, 0.1),
        "target": 1.0,
        "disturbance": -0.25,
        "sensor_noise": 0.08,
    }


def run(settings: dict):
    return run_feedback_mission("mission_3", settings)


def evaluate(result) -> MissionCheck:
    final_error = float(result.metrics["final_error"])
    mean_error = float(result.metrics["mean_absolute_error"])
    requirements = [
        RequirementResult("final_error", "Final error", final_error < 0.20, final_error, "< 0.20"),
        RequirementResult("mean_error", "Mean absolute error", mean_error < 0.30, mean_error, "< 0.30"),
    ]
    return MissionCheck(all(item.passed for item in requirements), "Control the complete imperfect system.", requirements)


MISSION = MissionDefinition(
    id="mission_3",
    title="Mission 3 — Complete system challenge",
    objective="Control the plant with both disturbance and sensor noise present.",
    render_controls=render_controls,
    run=run,
    evaluate=evaluate,
    reflection_prompts=(
        ReflectionPrompt("m3_evidence", "Use the metrics to justify why your final design is acceptable."),
        ReflectionPrompt("m3_limit", "Identify one limitation of this simulation or controller."),
    ),
)

