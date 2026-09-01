from __future__ import annotations

from lab.autosave import submission_root
from lab.final_reflection import render_final_reflection, write_final_reflection
from lab.session import response, set_response
from lab.submissions import write_foundations_summary, write_manifest
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
        "final.system_synthesis",
        "In 300–500 words, use your evidence to explain: why robotics software is difficult; which architecture you implemented and its trade-offs; how ROS 2 middleware connected at least four components through at least three communication relationships; how timing or invalid data affected safety; and which layer could restrict unsafe motion.",
        height=320,
    )
    synthesis_words = len(synthesis.split())
    st.caption(f"Integrated synthesis: {synthesis_words}/300–500 words")
    st.subheader("Technical exit explanations")
    reflections = [
        text_response(st, "final.architecture_evidence", "What evidence supports calling your node reactive, and what would have to be added for a genuinely hybrid system?"),
        text_response(st, "final.timing_evidence", "Which recorded timing or sensor-failure result most affected your understanding of robot safety?"),
        text_response(st, "final.middleware_debugging", "How would the ROS graph help you diagnose a command that never reaches the robot?"),
        text_response(st, "final.hardware_next", "What would you test next before using the behavior on hardware?"),
    ]
    course_reflection_ready = render_final_reflection(st)
    ready = 300 <= synthesis_words <= 500 and all(len(answer.strip()) >= 60 for answer in reflections) and course_reflection_ready
    if not ready:
        st.info("Complete the 300–500 word synthesis, technical exit explanations, and final reflection.")
        return
    write_foundations_summary(st)
    write_final_reflection(st)
    manifest = write_manifest(st)
    st.success("Your individual Git-ready submission is complete.")
    st.code(str(submission_root()))
    st.caption(f"Manifest: {manifest.name}")
    st.code(
        "git add student_submission ros2_ws/src/week01_behavior\n"
        "git commit -m \"Submit Week 1 ROS foundations lab\"\n"
        "git push",
        language="bash",
    )
