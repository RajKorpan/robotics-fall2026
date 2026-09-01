from __future__ import annotations

from lab.autosave import submission_root
from lab.final_reflection import render_final_reflection, write_final_reflection
from lab.navigation import set_stage
from lab.submissions import write_manifest
from lab_config import LAB


def render(st) -> None:
    st.title("Final submission")
    completed = set(st.session_state.get("completed_missions", []))
    missing = [mission for mission in LAB.missions if mission not in completed]
    if missing:
        st.warning(f"Complete these missions first: {', '.join(missing)}")
        if st.button("Back to lab"):
            set_stage(st, "lab")
        return

    if not render_final_reflection(st):
        return
    write_final_reflection(st)
    manifest = write_manifest(st)
    st.success("The Git-ready submission is complete.")
    st.code(str(submission_root()))
    st.caption(f"Manifest written to {manifest.name}.")
    st.markdown(
        "Commit the generated folder and submit the GitHub commit link:\n\n"
        "```bash\n"
        "git add student_submission\n"
        "git commit -m \"Submit robotics lab\"\n"
        "git push\n"
        "```"
    )
