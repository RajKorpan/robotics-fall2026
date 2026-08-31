from __future__ import annotations

from lab.navigation import set_stage


def render(st) -> None:
    st.title("Motion, Frames, and AI-Assisted ROS Development")
    st.write(
        "In this individual lab you will predict mobile-robot motion, interpret coordinates "
        "across ROS frames, and use an AI assistant while preserving and verifying its work."
    )
    st.markdown(
        "You will submit:\n"
        "- Predicted and observed robot poses\n"
        "- A documented TF tree and point transformations\n"
        "- Original AI prompt and output\n"
        "- Problems found, modifications, tests, and final ROS code\n"
        "- An individual correctness argument"
    )
    student = dict(st.session_state.get("student", {}))
    student["name"] = st.text_input("Full name", value=student.get("name", ""))
    student["email"] = st.text_input("Hunter email", value=student.get("email", ""))
    student["course_id"] = st.text_input("Course ID", value=student.get("course_id", ""))
    st.session_state["student"] = student
    if st.button("Begin", type="primary", disabled=not all(str(value).strip() for value in student.values())):
        set_stage(st, "concepts")

