from __future__ import annotations

from lab.navigation import set_stage


def render(st) -> None:
    st.title("Robotics Lab Template")
    st.write(
        "This runnable example demonstrates the standard structure for future labs: "
        "learn one concept, test it interactively, complete three measured missions, "
        "and submit automatically generated evidence."
    )
    st.subheader("Student information")
    student = dict(st.session_state.get("student", {}))
    student["name"] = st.text_input("Name", value=student.get("name", ""))
    student["email"] = st.text_input("Email", value=student.get("email", ""))
    st.session_state["student"] = student
    ready = bool(student["name"].strip() and student["email"].strip())
    st.info("Replace this page's copy with the topic, objectives, prior-knowledge connection, and evidence students will produce.")
    if st.button("Begin", type="primary", disabled=not ready):
        set_stage(st, "concepts")

