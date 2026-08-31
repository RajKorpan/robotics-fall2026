from lab.navigation import set_stage


def render(st):
    st.title("Week 11 — Human–Robot Interaction Evaluation")
    st.subheader("Prototype → user test → evidence → redesign → retest")
    st.write("You will evaluate a small ROS interaction in which a robot announces an approach, listens for a command, confirms what it understood, handles ambiguity or timeout, and responds. Your evidence must support a concrete redesign—not merely a list of design opinions.")
    st.info("This is an individual submission. For the two short test sessions, work with one classmate: they participate in your test and you participate in theirs. Do not merge data, code, analysis, or submissions.")
    st.markdown("**Estimated time:** 3–4 hours  \n**Peer participation:** approximately 15 minutes for each student's system  \n**Data rule:** random code and task observations only—no names, demographics, audio, video, photos, or sensitive notes  \n**Motion rule:** keep physical motion disabled during peer testing unless the instructor explicitly supervises it")
    student=dict(st.session_state["student"]); student["name"]=st.text_input("Name",value=student["name"]); student["email"]=st.text_input("CUNY email",value=student["email"]); st.session_state["student"]=student
    if st.button("Begin",type="primary",disabled=not all(v.strip() for v in student.values())): set_stage(st,"concepts")

