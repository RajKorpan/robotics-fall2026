from __future__ import annotations

from datetime import datetime, timezone
import math

from lab.evidence import evidence_id, motion_runs
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_1 import evaluate
from simulation.kinematics import SEQUENCES


def render(st) -> None:
    st.title("Mission 1: Predict and execute motion")
    st.write("Compute each final pose relative to the sequence's starting pose, then compare it with the recorded robot motion.")
    locked_at = str(response(st, "mission_1.predictions_locked_at", ""))
    predictions = dict(response(st, "mission_1.predictions", {}))
    descriptions = {
        "straight": "v=0.15 m/s for 3.0 s",
        "turn_then_drive": "ω=0.50 rad/s for π s, then v=0.15 m/s for 2.0 s",
        "arc": "v=0.15 m/s and ω=0.40 rad/s for 4.0 s",
    }
    for name in SEQUENCES:
        st.subheader(name.replace("_", " ").title())
        st.code(descriptions[name])
        prior = predictions.get(name, {})
        columns = st.columns(3)
        values = {}
        for column, axis, label in zip(columns, ("x", "y", "theta"), ("x (m)", "y (m)", "θ (rad)")):
            with column:
                values[axis] = st.number_input(
                    label,
                    value=float(prior.get(axis, 0.0)),
                    step=0.01,
                    disabled=bool(locked_at),
                    key=f"prediction.{name}.{axis}",
                )
        predictions[name] = values
    set_response(st, "mission_1.predictions", predictions)
    if not locked_at:
        if st.button("Lock predictions and reveal run commands", type="primary"):
            set_response(st, "mission_1.predictions_locked_at", datetime.now(timezone.utc).isoformat())
            st.rerun()
        st.info("Run commands remain hidden until your predictions are locked.")
    else:
        st.success(f"Predictions locked at {locked_at}.")
        for name in SEQUENCES:
            st.code(f"ros2 run course_motion_tools run_sequence --ros-args -p sequence_id:={name}", language="bash")

    runs = motion_runs()
    if runs:
        st.subheader("Recorded evidence")
        rows = []
        for run in runs:
            rows.append({
                "Sequence": run.get("sequence_id"),
                "Observed x": run.get("observed_pose", {}).get("x"),
                "Observed y": run.get("observed_pose", {}).get("y"),
                "Observed θ": run.get("observed_pose", {}).get("theta"),
                "Position error": run.get("position_error"),
                "Heading error": run.get("heading_error"),
                "Stopped": run.get("stop_sent"),
            })
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.warning("No motion-sequence evidence found.")
    if st.button("Refresh runs"):
        st.rerun()

    text_response(st, "mission_1.model_vs_observation", "How closely did the observed motion match the model?")
    text_response(st, "mission_1.largest_error", "Which sequence had the largest discrepancy? Cite its metrics.")
    text_response(st, "mission_1.error_source", "Distinguish a modeling/timing error from a localization or measurement error.")
    text_response(st, "mission_1.twice_distance", "What would you predict if the robot drove twice as long at the same straight velocity?")
    check = evaluate(runs, st.session_state.get("responses", {}))
    render_check(st, check)
    current_id = evidence_id(runs, predictions, locked_at)
    checked = st.session_state.get("checked_evidence_ids", {}).get("mission_1")
    if check.passed and checked != current_id and st.button("Check and save Mission 1", type="primary"):
        save_mission("mission_1", {"evidence_id": current_id, "runs": runs, "check": [item.__dict__ for item in check.requirements]}, st.session_state.get("responses", {}))
        complete_mission(st, "mission_1", current_id)
        st.rerun()
    if checked == current_id:
        st.success("This motion evidence is saved.")
        if st.button("Continue to Mission 2", type="primary"):
            set_stage(st, "mission_2")

