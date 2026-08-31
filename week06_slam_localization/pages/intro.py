from lab.navigation import set_stage
def render(st):
    st.title("Week 6: SLAM and Localization")
    st.markdown("In this individual lab, you will use ROS 2 packages to build and evaluate maps—not implement SLAM from scratch. You will then test what happens when localization begins with good, wrong, ambiguous, or degraded information.")
    st.info("This is individual work. Your maps, trials, explanations, and submission artifacts must come from your own runs.")
    st.subheader("Learning objectives")
    st.markdown("- Explain how LiDAR, odometry, transforms, pose estimates, and an occupancy grid interact.\n- Build and save a map using SLAM.\n- compare exploration strategies using quantitative and visual evidence.\n- Initialize and evaluate localization in a saved map.\n- Distinguish a pose estimate from certainty about that estimate.\n- Identify conditions under which a robot should admit it does not know where it is.")
    student = dict(st.session_state["student"])
    for key, label in (("name", "Full name"), ("email", "Hunter email"), ("course_id", "Course ID / roster identifier")): student[key] = st.text_input(label, student.get(key, ""))
    st.session_state["student"] = student
    if st.button("Begin", type="primary", disabled=not all(str(value).strip() for value in student.values())): set_stage(st, "concepts")
