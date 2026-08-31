from lab.navigation import set_stage


def render(st):
    st.title("Week 5: Sensors, Noise, and Uncertainty")
    st.markdown("Robots do not observe the world directly. In this individual lab, you will characterize imperfect measurements, design a filtering and fusion pipeline, and defend two safety policies.")
    st.info("Complete this lab individually. You may discuss concepts, but every response, configuration, and submitted artifact must be your own.")
    st.subheader("Learning objectives")
    st.markdown("- Distinguish noise, bias, quantization, outliers, and dropout.\n- Quantify uncertainty using sample statistics.\n- Explain the accuracy–responsiveness trade-off.\n- Evaluate decisions using false-safe and unnecessary-stop errors.\n- Justify why deployment context changes an acceptable policy.")
    student = dict(st.session_state["student"])
    student["name"] = st.text_input("Full name", student.get("name", ""))
    student["email"] = st.text_input("Hunter email", student.get("email", ""))
    student["course_id"] = st.text_input("Course ID / roster identifier", student.get("course_id", ""), help="This creates your repeatable scenario; it is not displayed to classmates.")
    st.session_state["student"] = student
    ready = all(str(value).strip() for value in student.values())
    if st.button("Begin sensor playground", type="primary", disabled=not ready): set_stage(st, "concepts")
