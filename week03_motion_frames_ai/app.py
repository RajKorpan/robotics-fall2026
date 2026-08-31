from __future__ import annotations

import argparse
import os

from lab.autosave import load_state, save
from lab.navigation import current_stage, render_progress, set_stage
from lab.session import initialize
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
    import tempfile
    from pathlib import Path
    from lab.ai_log import assigned_pattern
    from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3
    from simulation.kinematics import SEQUENCES, integrate_sequence

    locked = "2026-08-31T00:00:00+00:00"
    responses = {
        "mission_1.predictions": {name: integrate_sequence(segments) for name, segments in SEQUENCES.items()},
        "mission_1.predictions_locked_at": locked,
        **{f"mission_1.{key}": "Explanation" for key in m1.REFLECTIONS},
    }
    runs = [
        {"sequence_id": name, "captured_at": "2026-08-31T00:01:00+00:00", "completed": True, "stop_sent": True, "position_error": 0.02, "heading_error": 0.01}
        for name in SEQUENCES
    ]
    assert m1.evaluate(runs, responses).passed
    snapshot = {
        "captured_at": locked,
        "frames": ["odom", "base_link", "base_scan"],
        "transformed_points": {"one": {"x": 1.1, "y": 0.0}, "two": {"x": 2.0, "y": 1.0}},
    }
    responses.update({
        "mission_2.relationships": dict(m2.RELATIONSHIPS),
        "mission_2.diagnostics": dict(m2.DIAGNOSTICS),
        "mission_2.point_answers": dict(snapshot["transformed_points"]),
        **{f"mission_2.{key}": "Explanation" for key in m2.REFLECTIONS},
    })
    assert m2.evaluate(snapshot, responses).passed
    pattern = assigned_pattern("test-student")
    lock = {"pattern": pattern, "locked_at": locked, "prompt_sha256": "a", "output_sha256": "b", "integrity_valid": True}
    ai_result = {"pattern": pattern, "unit_tests_passed": True, "integration_passed": True, "commands_bounded": True, "final_stop_verified": True, "source_differs_from_original": True, "test_count": 7}
    responses.update({f"mission_3.{key}": "A substantive response explaining evidence and responsibility." * 2 for key in m3.REFLECTIONS})
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative in ("week03_pattern/pattern.py", "week03_pattern/pattern_node.py", "test/test_pattern.py"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# source\n" + "value = 1\n" * 30, encoding="utf-8")
        assert m3.evaluate(ai_result, lock, responses, root).passed
    print("Week 3 lab smoke test passed.")


def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title=LAB.title, page_icon="🧭", layout="wide")
    initialize(st)
    if not st.session_state.get("responses"):
        saved = load_state()
        st.session_state["responses"] = dict(saved.get("responses", {}))
        st.session_state["completed_missions"] = list(saved.get("completed_missions", []))
        st.session_state["checked_evidence_ids"] = dict(saved.get("checked_evidence_ids", {}))
        if saved.get("student") and not any(st.session_state["student"].values()):
            st.session_state["student"] = dict(saved["student"])
    with st.sidebar.expander("Instructor controls"):
        expected = os.environ.get(LAB.instructor_password_env, "frames-master")
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
        path = save(st)
        st.sidebar.caption(f"Auto-saved to {path.parent.name}/")
    except OSError as error:
        st.sidebar.error(f"Autosave failed: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=LAB.title)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    run_smoke_test() if args.smoke_test else run_streamlit_app()


if __name__ == "__main__":
    main()
