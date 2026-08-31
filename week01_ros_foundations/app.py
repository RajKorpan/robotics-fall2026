from __future__ import annotations

import argparse
import os

from lab.autosave import autosave, load_saved_state
from lab.navigation import current_stage, render_progress, set_stage
from lab.session import initialize_session
from lab_config import LAB
from pages import concepts, final, intro, mission_1, mission_2, mission_3, preflight


PAGES = {
    "intro": intro.render,
    "concepts": concepts.render,
    "preflight": preflight.render,
    "mission_1": mission_1.render,
    "mission_2": mission_2.render,
    "mission_3": mission_3.render,
    "final": final.render,
}


def run_smoke_test() -> None:
    from pathlib import Path
    from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3

    graph = {
        "captured_at": "2026-08-31T00:00:00Z",
        "nodes": [{"name": f"/node_{index}"} for index in range(5)] + [{"name": "/obstacle_guard"}],
        "topics": [
            {"name": name, "types": [kind]} for name, kind in m1.REQUIRED_TOPICS.items()
        ],
    }
    responses = {
        "mission_1.node_roles": {f"/node_{i}": "Infrastructure" for i in range(5)},
        "mission_1.topic_types": dict(m1.REQUIRED_TOPICS),
        "mission_1.connections": dict(m1.REQUIRED_CONNECTION_ANSWERS),
        **{f"mission_1.{key}": "Complete explanation" for key in m1.REFLECTION_KEYS},
    }
    assert m1.evaluate(graph, responses).passed
    trials = [
        {"trial_type": kind, "captured_at": "2026-08-31T00:01:00Z", "completed": True, "stop_sent": True, "linear_x": 0.1, "angular_z": 0.2}
        for kind in (*m2.TRIAL_TYPES, "curve_modified")
    ]
    responses.update({
        "mission_2.predictions": {kind: "Prediction" for kind in (*m2.TRIAL_TYPES, "curve_modified")},
        "mission_2.predictions_locked_at": "2026-08-31T00:00:00Z",
        "mission_2.target_reached": True,
        "mission_2.command_path": "A detailed command path explanation " * 4,
        **{f"mission_2.{key}": "Complete explanation" for key in m2.REFLECTION_KEYS},
    })
    assert m2.evaluate(trials, responses).passed
    behavior = {
        "unit_tests_passed": True,
        "command_bounded": True,
        "ros_node_verified": True,
        "scenarios": {name: {"passed": True} for name in m3.SCENARIOS},
    }
    responses.update({
        "mission_3.design": {key: "safe" for key in ("front_width", "stop_distance", "forward_speed", "invalid_policy", "stale_policy")},
        "mission_3.failure_investigation": "A documented prediction, observed failure, restoration, and explanation. " * 2,
        **{f"mission_3.{key}": "Complete explanation" for key in m3.REFLECTION_KEYS},
    })
    source = Path(__file__).resolve().parent / "ros2_ws" / "src" / "week01_behavior"
    assert m3.evaluate(behavior, graph, responses, source).passed
    print("Week 1 lab smoke test passed.")


def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title=LAB.title, page_icon="🤖", layout="wide")
    initialize_session(st)
    if not st.session_state.get("responses"):
        saved = load_saved_state()
        st.session_state["responses"] = dict(saved.get("responses", {}))
        st.session_state["completed_missions"] = list(saved.get("completed_missions", []))
        st.session_state["checked_evidence_ids"] = dict(saved.get("checked_evidence_ids", {}))
        if saved.get("student") and not any(st.session_state["student"].values()):
            st.session_state["student"] = dict(saved["student"])

    with st.sidebar.expander("Instructor controls"):
        expected = os.environ.get(LAB.instructor_password_env, "ros-master")
        password = st.text_input("Password", type="password")
        if password == expected:
            destination = st.selectbox("Jump to", LAB.stages)
            if st.button("Go"):
                set_stage(st, destination)
        else:
            st.caption("Locked")

    render_progress(st)
    PAGES[current_stage(st)](st)
    try:
        path = autosave(st)
        st.sidebar.caption(f"Auto-saved to {path.parent.name}/")
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
