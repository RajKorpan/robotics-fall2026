from lab.navigation import set_stage


def render(st):
    st.title("Week 9 — Planning and Human-Aware Navigation")
    st.subheader("A collision-free route is necessary. Is it sufficient?")
    st.write("You will use Nav2 to inspect candidate paths, execute repeatable navigation trials, then redesign a technically valid but socially inappropriate route. You are evaluating and configuring a navigation stack—not implementing a production planner.")
    st.info("This is an individual lab. You may help classmates troubleshoot the shared software environment, but every run, analysis, design choice, file, and submission must be your own.")
    st.markdown("**Estimated time:** 3–4 hours  \n**Prerequisites:** your Week 6 saved map and localization workflow; Week 8 camera concepts are helpful but no detector is required  \n**Final artifact:** raw JSON, checked evidence, RViz images, Nav2 configuration/masks, explanations, and one individual Git commit")
    name = st.text_input("Name", value=st.session_state["student"]["name"]); email = st.text_input("CUNY email", value=st.session_state["student"]["email"])
    st.session_state["student"] = {"name": name, "email": email}
    if st.button("Begin", type="primary", disabled=not (name.strip() and email.strip())): set_stage(st, "concepts")

