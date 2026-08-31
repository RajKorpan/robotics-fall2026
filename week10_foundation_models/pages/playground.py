from simulation.language import run_language_suite
from simulation.vision import run_vision_suite
from simulation.verification import run_verification_suite
from lab.navigation import set_stage


def render(st):
    st.header("Model sandbox")
    mode = st.radio("Explore", ["Language plans", "Vision-language scenes", "Verification policies"], horizontal=True)
    if mode == "Language plans": result = run_language_suite({"response_bank":"course-fm-1.0"})
    elif mode == "Vision-language scenes": result = run_vision_suite({"confidence_threshold": st.slider("Threshold", .3, .95, .65, .05)})
    else:
        result = run_verification_suite({"confidence_threshold": st.slider("Threshold", .3, .9, .65, .05), "validate_grounding": st.checkbox("Grounding check", True), "check_prerequisites": st.checkbox("Prerequisite check", True), "block_unsafe_actions": st.checkbox("Allowlist", True), "confirm_consequential": st.checkbox("Human confirmation", True), "fallback": "stop and request clarification"})
    st.dataframe(result.traces, hide_index=True, width="stretch"); st.json(result.metrics)
    if result.artifacts:
        chosen = st.selectbox("Inspect scene", list(result.artifacts)); st.image(result.artifacts[chosen], width="stretch")
    st.caption("Sandbox runs are exploratory. Save a checked run inside each mission for submission.")
    if st.button("Start Mission 1"): set_stage(st, "lab")

