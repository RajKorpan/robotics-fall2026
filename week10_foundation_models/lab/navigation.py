from lab_config import LAB
from lab.evidence import save_progress, saved_run
from lab.drafts import current, capture_inputs
from lab.guidance_config import GUIDED_COUNT


def unlocked(state, target):
    checked = bool(state.get("preflight")) and all(row["Ready"] for row in state["preflight"])
    if target in ("intro", "preflight"):
        return True
    if target == "guided":
        return checked
    taught = checked and state.get("tutorial_reviewed", 0) >= GUIDED_COUNT
    if target == "mission_1":
        return taught
    previous = {"mission_2": "mission_1", "mission_3": "mission_2", "final_submission": "mission_3"}.get(target)
    return bool(taught and previous and current(previous, state))

LABELS = {"intro": "Introduction", "preflight": "Preflight", "guided": "Guided learning", "mission_1": "Mission 1: language", "mission_2": "Mission 2: vision", "mission_3": "Mission 3: robot actions", "final_submission": "Synthesis and submission"}


def current_stage(st):
    return st.session_state.get("stage", "intro")


def jump(st, stage):
    capture_inputs(st.session_state)
    if not unlocked(st.session_state, stage):
        st.warning("Complete the current checks and save changes before continuing.")
        return
    st.session_state["stage"] = stage
    st.session_state["scroll_top"] = True
    try:
        save_progress(st.session_state)
    except OSError as error:
        st.error("Progress could not be saved. Keep the guide open and copy your latest answers to a backup. " + str(error))
        return
    st.rerun()


def set_stage(st, stage):
    jump(st, stage)


def bottom_nav(st, previous, following, next_disabled=False):
    st.divider()
    left, right = st.columns(2)
    if previous and left.button("Back to " + LABELS[previous], key="bottom_back", width="stretch"):
        jump(st, previous)
    if following and right.button("Next: " + LABELS[following], key="bottom_next", disabled=next_disabled, width="stretch"):
        jump(st, following)


def render_progress(st):
    stage = current_stage(st)
    index = LAB.stages.index(stage)
    st.progress((index + 1) / len(LAB.stages), text=f"{index + 1}/{len(LAB.stages)}: {LABELS[stage]}")
    with st.sidebar.expander("Lab navigation", expanded=True):
        for target in LAB.stages:
            enabled = unlocked(st.session_state, target)
            if st.button(LABELS[target], key="nav." + target, disabled=not enabled or stage == target, width="stretch"):
                jump(st, target)
