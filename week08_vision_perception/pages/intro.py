from lab.navigation import set_stage
def render(st):
    st.title("Week 8: Computer Vision and Learned Perception");st.markdown("In this individual lab, you will compare an inspectable classical detector with a frozen pretrained detector, then connect uncertain visual observations to bounded robot behavior.");st.info("Your parameters, runs, explanations, code changes, and submitted evidence must be your own. Do not record identifiable people or bystanders.")
    st.subheader("Learning objectives");st.markdown("- Build a color/threshold/contour pipeline.\n- Evaluate precision, recall, false positives, and false negatives.\n- Explain confidence-threshold trade-offs in learned perception.\n- Connect camera, perception, decision, and actuation through ROS.\n- Design safe behavior when visual evidence is missing, stale, or uncertain.\n- Identify environmental conditions that break apparent visual competence.")
    student=dict(st.session_state["student"])
    for key,label in (("name","Full name"),("email","Hunter email"),("course_id","Course ID / roster identifier")):student[key]=st.text_input(label,student.get(key,""))
    st.session_state["student"]=student
    if st.button("Begin",type="primary",disabled=not all(str(value).strip() for value in student.values())):set_stage(st,"concepts")
