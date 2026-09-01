from __future__ import annotations

from lab_config import LAB


def current_stage(st) -> str:
    stage = str(st.session_state.get("stage", LAB.stages[0]))
    return stage if stage in LAB.stages else LAB.stages[0]


def set_stage(st, stage: str) -> None:
    if stage not in LAB.stages:
        raise ValueError(f"Unknown stage: {stage}")
    st.session_state["stage"] = stage
    st.session_state["scroll_to_top_pending"] = True
    st.rerun()


def scroll_to_top_if_requested(st) -> None:
    if not st.session_state.pop("scroll_to_top_pending", False):
        return
    st.html(
        """
        <script>
        function scrollToTop() {
          window.scrollTo({ top: 0, left: 0, behavior: "instant" });
          document.documentElement.scrollTop = 0;
          document.body.scrollTop = 0;
        }
        setTimeout(scrollToTop, 30);
        setTimeout(scrollToTop, 180);
        </script>
        """,
        unsafe_allow_javascript=True,
    )


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
