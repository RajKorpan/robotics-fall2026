from lab.navigation import bottom_nav


def render(st):
    st.title("Lab 9: Investigating foundation models for robotics")
    st.write("How do training data, modalities, action representations and validation affect a robot's ability to interpret a task and act usefully?")
    st.write("Experiment with a local language model and a local vision-language model. Change a request, inspect the newly generated answer, and compare its claims with robot capabilities or visible image evidence. Then compare how different prompts guide a robot through a maze using one-cell directions.")
    st.table([{"Stage": "Guided learning", "You will": "Explore model roles, training data, actions and interfaces"}, {"Stage": "Mission 1", "You will": "Compare three robot-request answers, then write and test your own"}, {"Stage": "Mission 2", "You will": "Compare three questions about one workbench photo, then test your own"}, {"Stage": "Mission 3", "You will": "Compare three directional robot runs, then write your own prompt"}])
    st.write("Answers are saved as you work. Use each mission's Check and save button to retain its experiment evidence. Finish with one technical synthesis and the course reflection, inspect the complete ZIP, and commit your submission folder. Enter your name and email when finalizing.")
    bottom_nav(st, None, "preflight")
