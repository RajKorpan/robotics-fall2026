from lab_config import LAB
LABELS = {"intro": "Introduction", "concepts": "How SLAM works", "preflight": "ROS preflight", "mission_1": "Build a map", "mission_2": "Compare strategies", "mission_3": "Localize", "final": "Submit"}
def current_stage(st): return st.session_state.get("stage", LAB.stages[0])
def set_stage(st, stage): st.session_state["stage"] = stage; st.rerun()
def render_progress(st):
    index = LAB.stages.index(current_stage(st)); st.progress((index + 1) / len(LAB.stages), text=f"{index + 1}/{len(LAB.stages)} — {LABELS[current_stage(st)]}")
