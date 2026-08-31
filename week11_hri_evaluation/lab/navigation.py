from lab_config import LAB
LABELS = {"intro":"Introduction", "concepts":"HRI concepts", "preflight":"Protocol and ROS", "mission_1":"Prototype", "mission_2":"Baseline test", "mission_3":"Redesign and retest", "final":"Submit"}
def current_stage(st): return st.session_state.get("stage", LAB.stages[0])
def set_stage(st, stage): st.session_state["stage"] = stage; st.rerun()
def render_progress(st):
    i = LAB.stages.index(current_stage(st)); st.progress((i+1)/len(LAB.stages), text=f"{i+1}/{len(LAB.stages)} — {LABELS[current_stage(st)]}")

