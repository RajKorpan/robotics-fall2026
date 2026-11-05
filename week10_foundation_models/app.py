from __future__ import annotations

import argparse
from lab.evidence import load_progress, save_progress
from lab.navigation import current_stage, render_progress
from lab_config import LAB
from lab.drafts import capture_inputs
from lab.guidance_config import GUIDED_VERSION
from pages import intro, preflight, guided, investigation_1, investigation_2, investigation_3, final_submission

PAGES = {"intro": intro.render, "preflight": preflight.render, "guided": guided.render, "mission_1": investigation_1.render,
         "mission_2": investigation_2.render, "mission_3": investigation_3.render, "final_submission": final_submission.render}


def run_smoke_test():
    from lab.local_config import LANGUAGE_TASKS, VISION_TASKS, MODEL_CONFIG, scene_path
    assert len(LANGUAGE_TASKS) == len(VISION_TASKS) == 3
    assert all(scene_path(case).is_file() for case in VISION_TASKS)
    assert all(len(config["revision"]) == 40 for config in MODEL_CONFIG.values())
    from simulation.robot_room import initial_state, evaluate
    outcome = evaluate({"job_id": "smoke", "case": "clear", "output": "UP", "robot_state": initial_state()}, initial_state())
    assert outcome["after"]["position"] == [1, 6] and outcome["decision"] == "MOVE"
    print("Lab 9 investigation smoke test passed")


def run_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title, page_icon="🧠", layout="wide")
    if "initialized_v2" not in st.session_state:
        saved = load_progress()
        defaults = {"stage": "intro", "responses": {}, "student": {"name": "", "email": ""}, "tutorial_step": 0, "tutorial_reviewed": 0, "controls": {}, "response_widgets": [], "guided_seen": [], "guided_version": GUIDED_VERSION}
        for key, value in defaults.items():
            st.session_state[key] = saved[key] if saved.get(key) is not None else value
        if saved and saved.get("guided_version") != GUIDED_VERSION:
            st.session_state["tutorial_step"] = 0
            st.session_state["tutorial_reviewed"] = 0
            st.session_state["guided_seen"] = []
        st.session_state["guided_version"] = GUIDED_VERSION
        if st.session_state["stage"] not in PAGES:
            st.session_state["stage"] = "intro"
        st.session_state["initialized_v2"] = True
        st.session_state["scroll_top"] = True
        # Preflight is a fresh environment check, never an optimistic saved claim.
        if st.session_state["stage"] not in ("intro", "preflight"):
            st.session_state["resume_after_preflight"] = st.session_state["stage"]
            st.session_state["stage"] = "preflight"
    if st.session_state.pop("scroll_top", False):
        import streamlit.components.v1 as components
        components.html("""<script>const p=window.parent;const el=p.document.querySelector('[data-testid="stMain"]');if(el) el.scrollTo(0,0);p.scrollTo(0,0);</script>""", height=0)
    capture_inputs(st.session_state)
    for key, value in st.session_state["controls"].items():
        if key not in st.session_state:
            st.session_state[key] = value
    render_progress(st)
    st.session_state["field_hint_shown"] = False
    PAGES[current_stage(st)](st)
    try:
        capture_inputs(st.session_state)
        save_progress(st.session_state)
        st.session_state.pop("save_error", None)
        st.sidebar.caption("Answers saved locally. Use Check and save for experiment evidence.")
    except OSError as error:
        st.error("Saving failed. Keep this page open and copy your latest answers to a backup before restarting. " + str(error))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=LAB.title)
    parser.add_argument("--smoke-test", action="store_true")
    args, _ = parser.parse_known_args()
    if args.smoke_test:
        run_smoke_test()
    else:
        run_app()
