from __future__ import annotations

import argparse
import os

from lab.autosave import autosave, load_saved_state
from lab.navigation import current_stage, render_progress, scroll_to_top_if_requested, set_stage
from lab.session import initialize_session, sanitize_responses
from lab_config import LAB
from pages import final, intro, mission_1, mission_2, mission_3, part_1, part_2, part_3, preflight


PAGES = {
    "intro": intro.render,
    "part_1": part_1.render,
    "part_2": part_2.render,
    "part_3": part_3.render,
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
        "services": [{"name": "/reset_world", "types": ["std_srvs/srv/Empty"]}],
    }
    responses = {
        "mission_1.node_roles": {f"/node_{i}": "Infrastructure" for i in range(5)},
        "mission_1.pipeline_roles": {f"/node_{i}": "Support" for i in range(5)},
        "mission_1.topic_types": dict(m1.REQUIRED_TOPICS),
        "mission_1.connections": dict(m1.REQUIRED_CONNECTION_ANSWERS),
        "mission_1.service_example": {"name": "/reset_world", "type": "std_srvs/srv/Empty", "purpose": "Reset simulation state"},
        **{f"mission_1.{key}": "Complete explanation" for key in m1.REFLECTION_KEYS},
    }
    assert m1.evaluate(graph, responses).passed
    trials = [
        {
            "trial_type": kind,
            "captured_at": "2026-08-31T00:01:00Z",
            "completed": True,
            "stop_sent": True,
            "linear_x": 0.1,
            "angular_z": 0.2,
            "command_started_at": "2026-08-31T00:00:57Z",
            "zero_command_sent_at": "2026-08-31T00:01:00Z",
            "actual_command_duration": 3.0,
            "duration_error": 0.0,
        }
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
        "mission_3.architecture": "Reactive",
        **{f"mission_3.{key}": "Complete explanation" for key in m3.REFLECTION_KEYS},
    })
    source = Path(__file__).resolve().parent / "ros2_ws" / "src" / "week01_behavior"
    assert m3.evaluate(behavior, graph, responses, source).passed
    print("Week 1 lab smoke test passed.")


def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title=LAB.title, page_icon="🤖", layout="wide")
    initialize_session(st)
    st.markdown(
        """
        <style>
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="textarea"]:focus-within {
          border-color: #0f766e !important;
          box-shadow: 0 0 0 1px #0f766e !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if not st.session_state.get("responses"):
        saved = load_saved_state()
        st.session_state["responses"] = sanitize_responses(dict(saved.get("responses", {})))
        st.session_state["completed_missions"] = list(saved.get("completed_missions", []))
        st.session_state["checked_evidence_ids"] = dict(saved.get("checked_evidence_ids", {}))
        if saved.get("student") and not any(st.session_state["student"].values()):
            saved_student = dict(saved["student"])
            st.session_state["student"] = {
                "name": str(saved_student.get("name", "")),
                "email": str(saved_student.get("email", "")),
            }

    with st.sidebar.expander("Instructor controls"):
        expected = os.environ.get(LAB.instructor_password_env, "ros-master")
        password = st.text_input("Password", type="password")
        if password == expected:
            destination = st.selectbox("Jump to", LAB.stages)
            if st.button("Go"):
                set_stage(st, destination)
        else:
            st.caption("Locked")

    scroll_to_top_if_requested(st)
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
    # Streamlit and its AppTest runner may add their own process arguments.
    args, _ = parser.parse_known_args()
    if args.smoke_test:
        run_smoke_test()
    else:
        run_streamlit_app()


if __name__ == "__main__":
    main()
