from __future__ import annotations

from lab_config import LAB


LABELS = {
    "intro": "Introduction",
    "concepts": "Motion model",
    "preflight": "Environment",
    "mission_1": "Predict motion",
    "mission_2": "Frames",
    "mission_3": "AI-assisted development",
    "final": "Submit",
}


def current_stage(st) -> str:
    stage = str(st.session_state.get("stage", LAB.stages[0]))
    return stage if stage in LAB.stages else LAB.stages[0]


def set_stage(st, stage: str) -> None:
    if stage not in LAB.stages:
        raise ValueError(f"Unknown stage: {stage}")
    st.session_state["stage"] = stage
    st.rerun()


def render_progress(st) -> None:
    stage = current_stage(st)
    index = LAB.stages.index(stage)
    st.progress((index + 1) / len(LAB.stages), text=f"{index + 1}/{len(LAB.stages)} — {LABELS[stage]}")

