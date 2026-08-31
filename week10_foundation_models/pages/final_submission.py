from lab.autosave import submission_root
from lab.navigation import set_stage
from lab.session import set_response
from lab.submissions import write_manifest
from lab_config import LAB


def render(st):
    st.title("Final synthesis and submission")
    missing = [m for m in LAB.missions if m not in st.session_state["completed_missions"]]
    if missing:
        st.warning("Complete: " + ", ".join(missing))
        if st.button("Back to missions"): set_stage(st, "lab")
        return
    key = "final.synthesis"; answer = st.text_area("In 200–300 words: If a foundation model is unreliable, what system architecture allows it to remain useful in robotics? Use evidence from all three missions and identify residual risk.", value=st.session_state["responses"].get(key, ""), height=240); set_response(st, key, answer); words = len(answer.split()); st.caption(f"{words}/200–300 words")
    if st.button("Generate final manifest", type="primary", disabled=not 200 <= words <= 300):
        path = write_manifest(st); st.success(f"Git-ready submission created at {path.parent}")
    st.markdown("Submit the complete `student_submission/` directory and your individual Git commit. It must contain original output tables, configurations, scene artifacts, checked requirements, explanations, and `manifest.json`.")

