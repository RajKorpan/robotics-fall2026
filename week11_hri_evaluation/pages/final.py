from lab.submissions import manifest
from lab.ui import response
from lab_config import LAB


def render(st):
    st.header("Final synthesis and submission"); missing=[m for m in LAB.missions if m not in st.session_state["completed_missions"]]
    if missing: st.warning("Complete: "+", ".join(missing))
    response(st,"final.synthesis","In 200–300 words: What makes a robot interaction understandable, recoverable, and accessible? Use baseline and retest evidence while respecting the study's limitations.",200,240); words=len(st.session_state["responses"].get("final.synthesis","").split()); st.caption(f"{words}/200–300 words")
    if st.button("Generate final manifest",type="primary",disabled=bool(missing) or not 200<=words<=300): path=manifest(st); st.success(f"Submission ready at {path.parent}")
    st.markdown("Submit `student_submission/` and your individual Git commit. Before committing, search filenames and notes once more to ensure the participant cannot be identified.")
