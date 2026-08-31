from lab.submissions import write_manifest
from lab.ui import text_response
from lab_config import LAB
def render(st):
    st.header("Final synthesis and submission");missing=[mission for mission in LAB.missions if mission not in st.session_state["completed_missions"]]
    if missing:st.warning("Complete: "+", ".join(missing))
    text_response(st,"final.synthesis","In 200–300 words, answer: When does this robot's apparent ability to see break down? Connect environmental conditions, classical assumptions, learned confidence, downstream behavior, and safe fallback evidence.",height=220);words=len(str(st.session_state["responses"].get("final.synthesis","")).split());st.caption(f"{words} words")
    if st.button("Generate final manifest",type="primary",disabled=bool(missing) or not 200<=words<=300):path=write_manifest(st);st.success(f"Submission ready at {path.parent}")
    st.markdown("Submit the complete `student_submission/` directory and your individual Git commit. Confirm it contains raw CSV data, checked JSON evidence, representative successes and failures, explanations, and `manifest.json`.")
