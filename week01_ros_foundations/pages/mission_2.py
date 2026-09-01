from __future__ import annotations

from datetime import datetime, timezone

from lab.evidence import evidence_id, motion_trials
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_2 import evaluate


TRIALS = {
    "straight": (0.15, 0.0, 3.0),
    "rotation": (0.0, 0.5, 3.0),
    "curve": (0.15, -0.4, 4.0),
}


def render(st) -> None:
    st.title("Mission 2: Control the robot")
    st.write("Predict what velocity commands will do, run them, and compare the prediction with observed motion.")
    st.info("A velocity command tells the robot how to move now. It does not specify a destination.")
    st.code("ros2 interface show geometry_msgs/msg/Twist", language="bash")

    predictions = dict(response(st, "mission_2.predictions", {}))
    locked_at = str(response(st, "mission_2.predictions_locked_at", ""))
    for name, (linear, angular, duration) in TRIALS.items():
        st.subheader(f"{name.title()} trial")
        st.code(f"linear.x={linear:.2f} m/s, angular.z={angular:.2f} rad/s, duration={duration:.1f} s")
        key = f"prediction.{name}"
        value = st.text_area(
            "Predict the direction, path shape, and fields that will change.",
            value=str(predictions.get(name, "")),
            key=key,
            disabled=bool(locked_at),
        )
        predictions[name] = value
    set_response(st, "mission_2.predictions", predictions)

    st.subheader("Modified curve")
    modified_prediction = st.text_area(
        "Change either velocity and predict how the curve will change.",
        value=str(predictions.get("curve_modified", "")),
        key="prediction.curve_modified",
        disabled=bool(locked_at),
    )
    predictions["curve_modified"] = modified_prediction
    set_response(st, "mission_2.predictions", predictions)
    if not locked_at:
        if st.button(
            "Lock predictions and reveal commands",
            type="primary",
            disabled=not all(str(predictions.get(name, "")).strip() for name in (*TRIALS, "curve_modified")),
        ):
            set_response(st, "mission_2.predictions_locked_at", datetime.now(timezone.utc).isoformat())
            st.rerun()
        st.info("The experiment commands remain hidden until all four predictions are locked.")
    else:
        st.success(f"Predictions locked at {locked_at}.")
        for name, (linear, angular, duration) in TRIALS.items():
            st.code(
                "ros2 run course_lab_tools timed_twist --ros-args "
                f"-p trial_type:={name} -p linear_x:={linear} -p angular_z:={angular} -p duration:={duration}",
                language="bash",
            )
        st.code(
            "ros2 run course_lab_tools timed_twist --ros-args "
            "-p trial_type:=curve_modified -p linear_x:=YOUR_VALUE "
            "-p angular_z:=YOUR_VALUE -p duration:=4.0",
            language="bash",
        )

    trials = motion_trials()
    if trials:
        st.subheader("Recorded trials")
        st.dataframe(trials, hide_index=True, width="stretch")
        st.caption(
            "The trial records both the requested duration and the measured interval before the zero command. "
            "Displacement can differ from speed × time because commands, simulation, odometry, and physical response are not identical."
        )
    else:
        st.warning("No motion trials have been recorded yet.")
    if st.button("Refresh recorded trials"):
        st.rerun()

    st.subheader("Target-zone challenge")
    st.write(
        "Plan and execute a short sequence that stops the robot in the marked target zone without contacting the obstacle. "
        "This is an exploration challenge, not precise navigation."
    )
    text_response(st, "mission_2.target_plan", "Write your command plan before attempting the target.")
    reached = st.checkbox(
        "I stopped inside the target zone without collision and inspected the recorded trajectory.",
        value=bool(response(st, "mission_2.target_reached", False)),
    )
    set_response(st, "mission_2.target_reached", reached)

    st.subheader("Explain the command path")
    text_response(
        st,
        "mission_2.command_path",
        "Trace information from your trial tool through /student_cmd_vel, the guard, /cmd_vel, the simulator, and /odom.",
        height=130,
    )
    text_response(st, "mission_2.velocity_vs_destination", "Why is a velocity command not the same as a destination?")
    text_response(st, "mission_2.combined_velocity", "What happened when linear and angular velocity were both nonzero?")
    text_response(st, "mission_2.least_accurate", "Which prediction was least accurate, and what evidence shows that?")
    text_response(st, "mission_2.command_vs_motion", "What distinguishes the command sent from the motion achieved?")
    text_response(st, "mission_2.safe_stop", "Why must every timed trial end with a zero command?")
    text_response(
        st,
        "mission_2.timing_evidence",
        "Compare requested duration, actual command duration, duration error, expected linear travel, and observed displacement for at least two trials. What does the evidence establish?",
        height=150,
    )
    text_response(
        st,
        "mission_2.delay_risk",
        "Using the timing explorer from Part 1 and your trials, explain how response delay changes physical risk.",
    )
    text_response(
        st,
        "mission_2.stale_command",
        "Why should a distributed robot stop when velocity commands become stale, even if the last command was valid when published?",
    )

    check = evaluate(trials, st.session_state.get("responses", {}))
    render_check(st, check)
    current_id = evidence_id(trials, predictions, reached)
    checked_id = st.session_state.get("checked_evidence_ids", {}).get("mission_2")
    if check.passed and checked_id != current_id:
        if st.button("Check and save Mission 2", type="primary"):
            evidence = {"evidence_id": current_id, "trials": trials, "check": [item.__dict__ for item in check.requirements]}
            save_mission("mission_2", evidence, st.session_state.get("responses", {}))
            complete_mission(st, "mission_2", current_id)
            st.rerun()
    if checked_id == current_id:
        st.success("These motion trials are saved.")
        if st.button("Continue to Mission 3", type="primary"):
            set_stage(st, "mission_3")
