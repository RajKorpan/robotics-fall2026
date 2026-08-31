from lab.navigation import set_stage


def render(st):
    st.header("What makes an interaction understandable?")
    st.table([
        {"Property":"Intention visibility","Question":"Can the person tell what the robot will do before it moves or acts?"},
        {"Property":"Listening clarity","Question":"Can the person tell when and how to provide a command?"},
        {"Property":"Feedback","Question":"Does the system expose what it heard and what state it is in?"},
        {"Property":"Predictability","Question":"Do similar inputs produce understandable, consistent transitions?"},
        {"Property":"Recoverability","Question":"Can the person correct, cancel, retry, or stop without facilitator help?"},
        {"Property":"Accessibility","Question":"Is essential information and control available through more than one modality?"},
    ])
    st.code("robot intent → approach cue → LISTENING → command\n                                      ↓\n                         repeat interpretation\n                         ↙                  ↘\n                 correct / cancel          confirm\n                      ↓                       ↓\n                 LISTENING                 bounded action\n\ntimeout, ambiguity, or STOP → visible safe state → recovery instruction",language="text")
    st.warning("A participant's difficulty is evidence about the prototype and test context—not a deficit in the participant.")
    if st.button("Continue to protocol and ROS setup"): set_stage(st,"preflight")
