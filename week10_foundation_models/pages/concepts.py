from lab.navigation import set_stage


def render(st):
    st.header("Capability, reliability, and authority")
    st.markdown("A foundation model can produce plausible language or recognize familiar patterns across many tasks. That breadth does not establish that a specific output is grounded, executable, safe, or authorized.")
    st.table([
        {"Question":"Executable?","Evidence needed":"Every action exists; arguments match the robot API."},
        {"Question":"Grounded?","Evidence needed":"Objects, people, places, and current state are verified."},
        {"Question":"Complete?","Evidence needed":"Prerequisites, ordering, failure handling, and stopping conditions are explicit."},
        {"Question":"Safe and authorized?","Evidence needed":"Independent constraints, human authority, and bounded effects."},
        {"Question":"Reliable here?","Evidence needed":"Tests cover relevant ambiguity, shift, occlusion, and consequences."},
    ])
    st.warning("A model's numeric confidence is an output of the model/interface. It is not a probability certificate unless calibration has been established for the relevant deployment distribution.")
    if st.button("Continue"): set_stage(st, "background")

