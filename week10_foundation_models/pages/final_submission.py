from lab.evidence import atomic, export_zip, readiness, root, saved_run
from lab.final_reflection import render_final_reflection
from lab.navigation import bottom_nav
from pages.workflow import field


def render(st):
    st.title("Synthesis, reflection and submission")
    st.write("Bring together the language responses, image claims, and robot-action trials. Distinguish what the models proposed from the evidence available and what actually happened in the simulator.")
    checks = readiness(st.session_state)
    st.dataframe(checks, hide_index=True)
    answer = field(st, "final_synthesis", "Using evidence from all three missions, what did you learn about turning a model's response into useful robot behavior? Explain how your requests, visible evidence and action checks affected the results, and identify one remaining limitation.", height=210)
    st.caption("Use specific evidence from all three missions. Suggested length: 150 to 300 words.")
    reflection_ready = render_final_reflection(st)
    if "identity_name" not in st.session_state:
        st.session_state["identity_name"] = st.session_state["student"].get("name", "")
    if "identity_email" not in st.session_state:
        st.session_state["identity_email"] = st.session_state["student"].get("email", "")
    name = st.text_input("Name", key="identity_name")
    email = st.text_input("Student ID or email", key="identity_email")
    st.session_state["student"] = {"name": name, "email": email}
    ready = all(c["Ready"] for c in checks) and len(answer.split()) >= 60 and reflection_ready and bool(name.strip() and email.strip())
    if not ready:
        st.info("Save all three missions, write the synthesis with at least 60 words, complete the 1 to 300 word reflection and enter your name and student ID or email.")
    st.write("The complete submission includes model versions, prompts, generated answers, exact input images, directional robot actions, paths, before/after states and explanations. The ZIP is a backup of the submission folder, not a second assignment.")
    if st.button("Finalize complete submission", type="primary", disabled=not ready):
        from lab.evidence import write_json
        write_json(root() / "student.json", st.session_state["student"])
        atomic(root() / "technical_synthesis.md", answer.encode())
        reflection = st.session_state["responses"].get("final.course_reflection", "")
        atomic(root() / "final_reflection.md", reflection.encode())
        st.session_state["complete_zip"] = export_zip()
        st.session_state["final_signature"] = (name, email, answer, reflection, tuple(saved_run(m).get("run_id") for m in ("mission_1", "mission_2", "mission_3")))
    signature = (name, email, answer, st.session_state["responses"].get("final.course_reflection", ""), tuple(saved_run(m).get("run_id") for m in ("mission_1", "mission_2", "mission_3")))
    if ready and st.session_state.get("final_signature") == signature and st.session_state.get("complete_zip"):
        st.download_button("Download complete submission ZIP", st.session_state["complete_zip"], file_name="lab9_submission.zip", mime="application/zip")
        st.success("Complete submission saved at " + str(root()))
        st.write("Inspect the files and keep a backup. From the repository root, commit and push the submission folder, then submit the commit link.")
        st.code('git add week10_foundation_models/student_submission\ngit commit -m "Submit Lab 9"\ngit push', language="bash")
    bottom_nav(st, "mission_3", None)
