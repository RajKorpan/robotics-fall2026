from lab_config import LAB

LABELS = {"intro": "Introduction", "concepts": "Core concepts", "background": "System model", "playground": "Model sandbox", "lab": "Missions", "final_submission": "Submit"}


def current_stage(st): return st.session_state.get("stage", LAB.stages[0])
def set_stage(st, stage): st.session_state["stage"] = stage; st.rerun()
def render_progress(st):
    i = LAB.stages.index(current_stage(st)); st.progress((i + 1) / len(LAB.stages), text=f"{i+1}/{len(LAB.stages)} — {LABELS[current_stage(st)]}")
    with st.sidebar.expander("Lab navigation", expanded=True):
        for stage in LAB.stages:
            unlocked = stage in ("intro", "concepts", "background", "playground") or bool(st.session_state.get("student", {}).get("name"))
            if st.button(LABELS[stage], key=f"nav.{stage}", disabled=not unlocked or stage == current_stage(st), width="stretch"): set_stage(st, stage)

