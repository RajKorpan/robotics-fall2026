from __future__ import annotations

from lab.autosave import submission_root
from lab.final_reflection import render_final_reflection, write_final_reflection
from lab.session import response, set_response
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
        "final.system_synthesis",
        "Explain why the robot is a system of interacting components, not just a Python program. Use at least four components, three communication relationships, and one failure case.",
        height=220,
    )
    st.subheader("Individual exit reflection")
    reflections = [
        text_response(st, "final.useful_command", "Which ROS inspection command was most useful, and why?"),
        text_response(st, "final.initial_confusion", "What part of the system was initially confusing?"),
        text_response(st, "final.node_change", "What changed when you added your own node?"),
        text_response(st, "final.control_evidence", "What evidence shows your node—not teleoperation—controlled the robot?"),
        text_response(st, "final.hardware_next", "What would you test next before using the behavior on hardware?"),
    ]
    course_reflection_ready = render_final_reflection(st)
    ready = len(synthesis.strip()) >= 250 and all(answer.strip() for answer in reflections) and course_reflection_ready
    if not ready:
        st.info("Complete the synthesis, technical exit reflections, and final reflection.")
        return
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
