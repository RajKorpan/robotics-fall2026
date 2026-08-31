from lab.navigation import set_stage


def render(st):
    st.title("Week 10 — Foundation Models for Robotics")
    st.subheader("Useful proposals are not permission to act")
    st.write("You will test a controlled language/vision model interface, locate grounding and capability failures, and place a verification layer between model proposals and robot actions. The goal is capability-versus-reliability reasoning—not model training or prompt tricks.")
    st.info("This is an individual lab. All experiments, explanations, configurations, and submitted evidence must be your own.")
    st.markdown("**Estimated time:** 2.5–3.5 hours  \n**Environment:** self-contained Python + Streamlit; no ROS, API key, account, or network access  \n**Submit:** original controlled outputs, measured comparisons, final verifier configuration, explanations, and manifest")
    student = dict(st.session_state["student"]); student["name"] = st.text_input("Name", value=student["name"]); student["email"] = st.text_input("CUNY email", value=student["email"]); st.session_state["student"] = student
    if st.button("Begin", type="primary", disabled=not all(v.strip() for v in student.values())): set_stage(st, "concepts")

