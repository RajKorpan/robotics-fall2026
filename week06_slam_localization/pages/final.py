from lab.final_reflection import render_final_reflection, write_final_reflection
from lab.submissions import write_manifest
from lab.ui import text_response
from lab_config import LAB
def render(st):
    st.header("Final synthesis and submission")
    missing = [mission for mission in LAB.missions if mission not in st.session_state["completed_missions"]]
    if missing: st.warning("Complete: " + ", ".join(missing))
    text_response(st, "final.synthesis", "In 200–300 words, answer: What does it mean for this robot to know where it is? Connect mapping strategy, loop closure, initial pose, sensor quality, uncertainty, and evidence from your runs.", height=220)
    words = len(str(st.session_state["responses"].get("final.synthesis", "")).split()); st.caption(f"{words} words")
    reflection_ready = render_final_reflection(st)
    if st.button("Generate final manifest", type="primary", disabled=bool(missing) or not 200 <= words <= 300 or not reflection_ready):
        write_final_reflection(st); path = write_manifest(st); st.success(f"Submission ready at {path.parent}")
    st.markdown("Submit the complete `student_submission/` directory. Confirm that both map pairs, evidence JSON files, screenshots, written explanations, and `manifest.json` are present. Also commit the folder to your individual Git repository.")
