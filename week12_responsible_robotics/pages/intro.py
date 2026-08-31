from lab.navigation import set_stage
def render(st):
    st.title("Week 12 — Responsible Robotics by Design"); st.subheader("A principle matters when it changes system behavior")
    st.write("You will configure an assistive/service robot and observe the measurable consequences of privacy, fairness, safety, accessibility, and human-control decisions. Some configurations fail. Revise them until they meet explicit requirements.")
    st.info("This is an individual, self-contained lab. It is an engineering design exercise—not another ethics audit and not proof that a deployed system is responsible.")
    st.markdown("**Estimated time:** 3–4 hours  \n**Environment:** Python + Streamlit; no ROS or network access  \n**Submit:** exact passing configurations, raw scenario tables, metrics, explanations, and manifest")
    student=dict(st.session_state["student"]); student["name"]=st.text_input("Name",value=student["name"]); student["email"]=st.text_input("CUNY email",value=student["email"]); st.session_state["student"]=student
    if st.button("Begin",type="primary",disabled=not all(v.strip() for v in student.values())): set_stage(st,"concepts")

