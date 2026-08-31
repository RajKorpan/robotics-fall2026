from lab.navigation import set_stage


def render(st):
    st.header("A safer system boundary")
    st.code("human request + sensed scene + world state\n                    ↓\n          foundation model (proposes)\n                    ↓\n       structured action plan + confidence\n                    ↓\n   schema → grounding → prerequisites → policy\n                    ↓\n      EXECUTE | CONFIRM | ABSTAIN | REJECT\n                    ↓\n        bounded robot skill + monitoring\n                    ↓\n        stop / recover / request help", language="text")
    st.write("The model does not write directly to actuators. Deterministic checks constrain vocabulary and arguments, live state validates prerequisites, policy reserves consequential decisions, and runtime monitoring can stop even an initially approved action.")
    st.markdown("The course response bank is deliberately imperfect and versioned. It makes failures reproducible and keeps private data off external services. Treat its outputs as test fixtures representing model behavior, not as claims about every commercial model.")
    if st.button("Open the sandbox"): set_stage(st, "playground")

