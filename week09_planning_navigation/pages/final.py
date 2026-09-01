from lab.final_reflection import render_final_reflection, write_final_reflection
from lab.submissions import write_manifest
from lab.ui import text_response
from lab_config import LAB


def render(st):
    st.header("Final synthesis and submission")
    missing = [m for m in LAB.missions if m not in st.session_state["completed_missions"]]
    if missing: st.warning("Complete: " + ", ".join(missing))
    text_response(st, "final.synthesis", "In 200–300 words: When is navigation successful? Connect plan feasibility, execution evidence, localization/sensing limits, human context, and your redesign trade-offs.", minimum_words=200, height=220)
    words = len(st.session_state["responses"].get("final.synthesis", "").split()); st.caption(f"{words}/200–300 words")
    reflection_ready = render_final_reflection(st)
    if st.button("Generate final manifest", type="primary", disabled=bool(missing) or not 200 <= words <= 300 or not reflection_ready):
        write_final_reflection(st); path = write_manifest(st); st.success(f"Submission ready: {path.parent}")
    st.markdown("Submit the complete `student_submission/` directory and the Git commit hash for your individual work. Verify that raw and checked JSON, configuration/masks, representative images, responses, and `manifest.json` are included.")
