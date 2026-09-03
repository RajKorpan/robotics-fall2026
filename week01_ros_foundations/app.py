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
    import tempfile
    from pathlib import Path
    from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3

    graph = {
        "captured_at": "2026-08-31T00:00:00Z",
        "nodes": [
            {"name": "/course_cmd_vel_guard"},
            {"name": "/course_evidence_collector"},
            {"name": "/ros_gz_bridge"},
            {"name": "/rviz2"},
        ],
        "topics": [
            {
                "name": name,
                "types": [kind],
                "publishers": ["/sensor"] if name in ("/scan", "/odom") else ["/guard"] if name == "/cmd_vel" else [],
                "subscribers": ["/behavior"] if name in ("/scan", "/odom") else ["/guard"] if name == "/student_cmd_vel" else ["/controller"],
            }
            for name, kind in m1.REQUIRED_TOPICS.items()
        ],
    }
    responses = {
        "mission_1.guided_checks": {key: True for key in m1.GUIDED_CHECKS},
        "mission_1.scan_observation": "I found the ranges field, which contains LiDAR distances in meters.",
        **{f"mission_1.{key}": "A complete explanation grounded in several live nodes, topics, and endpoint relationships." for key in m1.SYNTHESIS_KEYS},
    }
    assert m1.evaluate(graph, responses).passed
    trial_specs = {
        "straight": (0.15, 0.0, 3.0),
        "rotation": (0.0, 0.5, 3.0),
        "curve": (0.15, -0.4, 4.0),
        "curve_modified": (0.12, 0.6, 4.0),
    }
    trials = [
        {
            "trial_type": kind,
            "captured_at": "2026-08-31T00:01:00Z",
            "completed": True,
            "stop_sent": True,
            "linear_x": values[0],
            "angular_z": values[1],
            "duration": values[2],
            "command_started_at": "2026-08-31T00:00:57Z",
            "zero_command_sent_at": "2026-08-31T00:01:00Z",
            "actual_command_duration": 3.0,
            "duration_error": 0.0,
            "observed_path_length": 0.02 if kind == "rotation" else 0.4,
            "displacement": 0.01 if kind == "rotation" else 0.3,
            "heading_change": 1.0 if kind in ("rotation", "curve", "curve_modified") else 0.01,
        }
        for kind, values in trial_specs.items()
    ]
    responses.update({
        "mission_2.predictions": {kind: "A complete prediction written before running this motion trial." for kind in m2.TRIAL_TYPES},
        "mission_2.prediction_locks": {kind: "2026-08-31T00:00:00Z" for kind in m2.TRIAL_TYPES},
        "mission_2.modified_settings": {"linear_x": 0.12, "angular_z": 0.6, "duration": 4.0},
        **{f"mission_2.{key}": "A complete explanation grounded in the recorded measurements and safety behavior." for key in m2.SYNTHESIS_KEYS},
    })
    assert m2.evaluate(trials, responses).passed
    behavior = {
        "unit_tests_passed": True,
        "command_bounded": True,
        "ros_node_verified": True,
        "scenarios": {name: {"passed": True} for name in m3.SCENARIOS},
    }
    responses.update({
        **{f"mission_3.{key}": "A complete explanation of the implemented robot system." for key in m3.EXPLANATION_KEYS},
    })
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory)
        decision = source / "week01_behavior" / "decision.py"
        wrapper = source / "week01_behavior" / "obstacle_guard.py"
        student_test = source / "test" / "test_student_decision.py"
        for path in (decision, wrapper, student_test):
            path.parent.mkdir(parents=True, exist_ok=True)
        decision.write_text("def front_distance(): pass\ndef decide_velocity(): pass\n", encoding="utf-8")
        wrapper.write_text("# supplied ROS wrapper\n", encoding="utf-8")
        student_test.write_text(
            "from week01_behavior.decision import decide_velocity\n"
            "def test_student_decision():\n    assert decide_velocity(0.5, 0.5, 0.08) == 0.0\n"
            + "# student test explanation\n" * 3,
            encoding="utf-8",
        )
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
