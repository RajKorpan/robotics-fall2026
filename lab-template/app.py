from __future__ import annotations

import argparse

from lab.autosave import autosave_responses, load_responses
from lab.instructor import render_instructor_controls
from lab.navigation import current_stage, render_progress
from lab.session import initialize_session
from lab_config import LAB
from pages import background, concepts, final_submission, intro, missions, playground


PAGE_RENDERERS = {
    "intro": intro.render,
    "concepts": concepts.render,
    "background": background.render,
    "playground": playground.render,
    "lab": missions.render,
    "final_submission": final_submission.render,
}


def run_smoke_test() -> None:
    from missions import MISSIONS

    passing_settings = {
        "mission_1": {"gain": 1.0, "target": 1.0, "disturbance": 0.0, "sensor_noise": 0.0},
        "mission_2": {"gain": 2.0, "target": 1.0, "disturbance": -0.35, "sensor_noise": 0.0},
        "mission_3": {"gain": 2.0, "target": 1.0, "disturbance": -0.25, "sensor_noise": 0.08},
    }
    for mission_id in LAB.missions:
        mission = MISSIONS[mission_id]
        result = mission.run(passing_settings[mission_id])
        check = mission.evaluate(result)
        if not result.traces or not check.requirements:
            raise AssertionError(f"{mission_id} did not produce a complete result")
        print(f"{mission_id}: {'PASS' if check.passed else 'valid run'} — {result.metrics}")
    print("Smoke test passed.")


def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title=LAB.title, page_icon="🤖", layout="wide")
    initialize_session(st)
    if not st.session_state.get("responses"):
        saved = load_responses()
        st.session_state["responses"] = dict(saved.get("responses", {}))
        if saved.get("student") and not any(st.session_state["student"].values()):
            st.session_state["student"] = dict(saved["student"])

    render_instructor_controls(st)
    render_progress(st)
    PAGE_RENDERERS[current_stage(st)](st)
    try:
        path = autosave_responses(st)
        st.sidebar.caption(f"Responses auto-saved to {path.parent.name}/")
    except OSError as error:
        st.sidebar.error(f"Autosave failed: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=LAB.title)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        run_smoke_test()
    else:
        run_streamlit_app()


if __name__ == "__main__":
    main()

