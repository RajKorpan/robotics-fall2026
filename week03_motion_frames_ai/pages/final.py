from __future__ import annotations

from lab.autosave import submission_root
from lab.submissions import write_manifest
from lab.ui import text_response
from lab_config import LAB


def render(st) -> None:
    st.title("Final synthesis and submission")
    missing = [mission for mission in LAB.missions if mission not in st.session_state.get("completed_missions", [])]
    if missing:
        st.warning(f"Complete these missions first: {', '.join(missing)}")
        return
    synthesis = text_response(
        st,
        "final.synthesis",
        "Explain how motion models, coordinate frames, and software tests provide different kinds of evidence about robot behavior.",
        height=220,
    )
    reflections = [
        text_response(st, "final.model_surprise", "What most surprised you about predicted versus observed motion?"),
        text_response(st, "final.frame_insight", "What frame mistake now seems most likely in future ROS work?"),
        text_response(st, "final.ai_judgment", "What did you—not the AI assistant—contribute to the final program's correctness?"),
    ]
    if len(synthesis.strip()) < 250 or not all(value.strip() for value in reflections):
        st.info("Complete the synthesis (at least 250 characters) and all reflections.")
        return
    manifest = write_manifest(st)
    st.success("Your individual Git-ready submission is complete.")
    st.code(str(submission_root()))
    st.caption(f"Manifest: {manifest.name}")
    st.code(
        "git add student_submission ros2_ws/src/week03_pattern\n"
        "git commit -m \"Submit Week 3 motion, frames, and AI lab\"\n"
        "git push",
        language="bash",
    )

