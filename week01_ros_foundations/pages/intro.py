from __future__ import annotations

from lab.navigation import set_stage


def render(st) -> None:
    st.title("Discovering a Robot Through ROS 2")
    st.markdown(
        "A mobile robot is not one Python program. It is a system of components that "
        "sense, communicate, decide, and act. In this lab you will inspect that system, "
        "compare ways to organize it, control it, and add one new decision-making component."
    )
    st.info("This is an individual lab. Every prediction, run, code change, and explanation must be your own.")
    st.subheader("What you will produce")
    st.markdown(
        "- A completion record from three guided visual tutorials\n"
        "- A ROS node/topic system diagram\n"
        "- Predicted-versus-observed motion evidence\n"
        "- A tested obstacle-stop ROS node\n"
        "- Individual explanations and a Git-ready submission"
    )
    student = dict(st.session_state.get("student", {}))
    student["name"] = st.text_input("Full name", value=student.get("name", ""))
    student["email"] = st.text_input("Hunter email", value=student.get("email", ""))
    st.session_state["student"] = {"name": student["name"], "email": student["email"]}
    ready = all(str(value).strip() for value in st.session_state["student"].values())
    if st.button("Begin lab", type="primary", disabled=not ready):
        set_stage(st, "part_1")
