from __future__ import annotations

from lab_config import LAB


def current_stage(st) -> str:
    stage = str(st.session_state.get("stage", LAB.stages[0]))
    return stage if stage in LAB.stages else LAB.stages[0]


def set_stage(st, stage: str) -> None:
    if stage not in LAB.stages:
        raise ValueError(f"Unknown stage: {stage}")
    st.session_state["stage"] = stage
    st.rerun()


def next_stage(stage: str) -> str | None:
    index = LAB.stages.index(stage)
    return LAB.stages[index + 1] if index + 1 < len(LAB.stages) else None


def render_progress(st) -> None:
    stage = current_stage(st)
    index = LAB.stages.index(stage)
    st.progress((index + 1) / len(LAB.stages), text=f"Stage {index + 1} of {len(LAB.stages)}")

