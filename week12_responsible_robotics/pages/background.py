from lab.navigation import set_stage
def render(st):
    st.header("Configurable assistive-robot architecture")
    st.code("sensors → local feature extraction → perception score\n   │                                  ↓\n   └─ data policy             threshold / abstain\n       consent                     ↓        ↓\n       storage                 decision   review\n       deletion                    ↓\n                          safety + access policy\n                    speed · distance · confirmation\n                    feedback · stop · local fallback\n                                  ↓\n                            bounded robot action",language="text")
    st.write("The three missions touch different parts of one system. Minimizing data can change utility. Improving subgroup performance can increase review workload. Conservative safety policies can reduce speed or autonomy. Responsible design makes these choices explicit, measurable, and revisable.")
    if st.button("Open policy sandbox"): set_stage(st,"playground")

