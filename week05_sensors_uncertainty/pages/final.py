from pathlib import Path

from lab.submissions import write_manifest
from lab.ui import text_response
from lab_config import LAB


def render(st):
    st.header("Final synthesis and submission")
    completed = set(st.session_state["completed_missions"]); missing = [mission for mission in LAB.missions if mission not in completed]
    if missing: st.warning("Return to the unfinished missions: " + ", ".join(missing))
    text_response(st, "final.synthesis", "In 150–250 words, explain how measurement properties, estimation choices, and deployment context connect. Cite evidence from all three missions.", height=180)
    synthesis = str(st.session_state["responses"].get("final.synthesis", "")).strip(); words = len(synthesis.split())
    st.caption(f"Synthesis length: {words} words")
    ready = not missing and 150 <= words <= 250
    if st.button("Generate final manifest", type="primary", disabled=not ready):
        path = write_manifest(st); st.success(f"Submission ready: {path.parent}")
    root = Path(__file__).resolve().parents[1] / LAB.submission_directory
    st.markdown("Submit the entire `student_submission/` directory. It must contain `student.json`, `manifest.json`, the three mission folders, and the autosave folder. Open the generated files before submitting and confirm they contain your work.")
    if (root / "manifest.json").exists(): st.code(str(root), language=None)
