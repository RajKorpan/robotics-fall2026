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


def render_progress(st) -> None:
    stage = current_stage(st)
    index = LAB.stages.index(stage)
    labels = {
        "intro": "Introduction",
        "part_1": "Why robotics is difficult",
        "part_2": "Robot architectures",
        "part_3": "What ROS 2 provides",
        "preflight": "Environment check",
        "mission_1": "Observe",
        "mission_2": "Control",
        "mission_3": "Create behavior",
        "final": "Submit",
    }
    st.progress((index + 1) / len(LAB.stages), text=f"{index + 1}/{len(LAB.stages)} — {labels[stage]}")
