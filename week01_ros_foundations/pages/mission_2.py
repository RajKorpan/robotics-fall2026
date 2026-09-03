from __future__ import annotations

import math
import os
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from lab.evidence import evidence_id, motion_trials
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_2 import TRIAL_TYPES, evaluate, mission_responses, motion_observed


ROOT = Path(__file__).resolve().parents[1]
FIXED_TRIALS = {
    "straight": {
        "title": "Straight motion",
        "linear_x": 0.15,
        "angular_z": 0.0,
        "duration": 3.0,
        "teaching": "Forward speed is positive and turning speed is zero, so the robot should travel straight ahead.",
        "prompt": "Where will the robot finish relative to its starting point? Sentence starter: I predict the robot will...",
    },
    "rotation": {
        "title": "Rotation in place",
        "linear_x": 0.0,
        "angular_z": 0.5,
        "duration": 3.0,
        "teaching": "Forward speed is zero and turning speed is positive, so the robot should turn left without intentionally traveling forward.",
        "prompt": "How will the robot's position and direction change? Sentence starter: I predict its position will... while its direction will...",
    },
    "curve": {
        "title": "Curved motion",
        "linear_x": 0.15,
        "angular_z": -0.4,
        "duration": 4.0,
        "teaching": "The robot moves forward while turning right, so its path should form a right-hand curve.",
        "prompt": "What path shape and turn direction do you expect? Sentence starter: I predict a... because...",
    },
}


def _motion_path(linear_x: float, angular_z: float, duration: float) -> tuple[str, float, float, float]:
    x, y, heading = 100.0, 130.0, 0.0
    points = [(x, y)]
    steps = 60
    scale = 380.0
    for _ in range(steps):
        interval = duration / steps
        x += linear_x * math.cos(heading) * interval * scale
        y -= linear_x * math.sin(heading) * interval * scale
        heading += angular_z * interval
        points.append((x, y))
    path = " ".join(("M" if index == 0 else "L") + f" {px:.1f} {py:.1f}" for index, (px, py) in enumerate(points))
    return path, x, y, heading


def _motion_preview(st, linear_x: float, angular_z: float, duration: float, label: str) -> None:
    path, end_x, end_y, heading = _motion_path(linear_x, angular_z, duration)
    if abs(linear_x) < 1e-9:
        robot = f"""
        <g>
          <animateTransform attributeName="transform" type="rotate" from="0 100 130" to="{-math.degrees(heading):.1f} 100 130" dur="2.8s" repeatCount="indefinite" />
          <rect x="78" y="114" width="44" height="32" rx="8" fill="#38bdf8" stroke="#075985" stroke-width="3" />
          <path d="M92 130 L113 130 M106 123 L114 130 L106 137" stroke="#082f49" stroke-width="3" fill="none" />
        </g>"""
    else:
        robot = f"""
        <g>
          <animateMotion path="{path}" dur="2.8s" repeatCount="indefinite" rotate="auto" />
          <rect x="-22" y="-16" width="44" height="32" rx="8" fill="#38bdf8" stroke="#075985" stroke-width="3" />
          <path d="M-8 0 L13 0 M6 -7 L14 0 L6 7" stroke="#082f49" stroke-width="3" fill="none" />
        </g>"""
    st.html(
        f"""
        <div style="border:1px solid #cbd5e1;border-radius:12px;padding:10px;background:#f8fafc">
          <div style="font-weight:700;margin-bottom:4px">{label}</div>
          <svg viewBox="0 0 560 260" style="width:100%;height:220px;background:#0f172a;border-radius:9px">
            <defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#334155" stroke-width="1" /></pattern></defs>
            <rect width="560" height="260" fill="url(#grid)" />
            <path d="{path}" fill="none" stroke="#facc15" stroke-width="5" stroke-dasharray="8 7" />
            <circle cx="100" cy="130" r="7" fill="#4ade80" />
            <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="7" fill="#fb7185" />
            {robot}
            <text x="18" y="25" fill="#cbd5e1" font-size="14">green: start   pink: predicted end</text>
          </svg>
        </div>
        """
    )


def _trial_after_lock(trial: dict, locked_at: str) -> bool:
    return bool(
        trial
        and trial.get("completed")
        and trial.get("stop_sent")
        and motion_observed(str(trial.get("trial_type", "")), trial)
        and locked_at
        and str(trial.get("captured_at", "")) >= locked_at
    )


def _run_trial(name: str, linear_x: float, angular_z: float, duration: float) -> tuple[bool, str]:
    started_at = datetime.now(timezone.utc).isoformat()
    command = (
        "source /opt/ros/jazzy/setup.bash && "
        "source /workspace/week01_ros_foundations/ros2_ws/install/setup.bash && "
        "export ROS_DOMAIN_ID=24 && "
        "export WEEK01_EVIDENCE_DIR=/workspace/week01_ros_foundations/runtime/evidence && "
        "gz service -s /world/default/set_pose/blocking --reqtype gz.msgs.Pose "
        "--reptype gz.msgs.Boolean --timeout 5000 "
        "--req 'name: \"burger\", position: {x: -2.0, y: -0.5, z: 0.01}, orientation: {w: 1.0}' && "
        "sleep 1 && "
        "ros2 run course_lab_tools timed_twist --ros-args "
        f"-p trial_type:={name} -p linear_x:={linear_x:.4f} "
        f"-p angular_z:={angular_z:.4f} -p duration:={duration:.1f}"
    )
    process = None
    try:
        process = subprocess.Popen(
            ["bash", "-lc", command],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=duration + 20.0)
    except subprocess.TimeoutExpired:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=3.0)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except OSError:
                    pass
                stdout, stderr = process.communicate()
        else:
            stdout, stderr = "", ""
        recorded = next(
            (
                trial
                for trial in motion_trials()
                if trial.get("trial_type") == name
                and str(trial.get("captured_at", "")) >= started_at
                and trial.get("completed")
                and trial.get("stop_sent")
                and motion_observed(name, trial)
            ),
            None,
        )
        if recorded:
            return True, "The robot moved, stopped, and saved the required measurements. The trial helper took extra time to close, so the guide closed it after preserving the successful result."
        output = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
        return False, output or "The trial timed out before complete motion and stop evidence were saved."
    except OSError as error:
        return False, f"The trial could not start: {error}"
    output = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    if process is None or process.returncode != 0:
        return False, output or f"The trial exited with code {process.returncode if process else 'unknown'}."
    return True, output or "The trial completed and its evidence was saved."


def _reset_robot() -> tuple[bool, str]:
    command = (
        "source /opt/ros/jazzy/setup.bash && "
        "source /workspace/week01_ros_foundations/ros2_ws/install/setup.bash && "
        "export ROS_DOMAIN_ID=24 && "
        "ros2 topic pub --once /student_cmd_vel geometry_msgs/msg/Twist "
        "'{linear: {x: 0.0}, angular: {z: 0.0}}' >/dev/null && "
        "gz service -s /world/default/set_pose/blocking --reqtype gz.msgs.Pose "
        "--reptype gz.msgs.Boolean --timeout 5000 "
        "--req 'name: \"burger\", position: {x: -2.0, y: -0.5, z: 0.01}, orientation: {w: 1.0}'"
    )
    try:
        result = subprocess.run(
            ["bash", "-lc", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"The robot could not be reset: {error}"
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode != 0:
        return False, output or "The robot reset command failed."
    return True, "The robot stopped and returned to the starting position for Mission 3."


def _result_row(name: str, trial: dict) -> dict:
    return {
        "Trial": name.replace("_", " ").title(),
        "Forward speed (m/s)": round(float(trial.get("linear_x", 0.0)), 3),
        "Turning speed (rad/s)": round(float(trial.get("angular_z", 0.0)), 3),
        "Requested time (s)": round(float(trial.get("duration", 0.0)), 3),
        "Actual command time (s)": round(float(trial.get("actual_command_duration", 0.0)), 3),
        "Commanded path length (m)": round(float(trial.get("commanded_path_length", trial.get("expected_linear_travel", 0.0))), 3),
        "Estimated traveled path (m)": round(float(trial.get("observed_path_length", trial.get("displacement", 0.0))), 3),
        "Start-to-end distance (m)": round(float(trial.get("displacement", 0.0)), 3),
        "Direction change (degrees)": round(math.degrees(float(trial.get("heading_change", 0.0))), 1),
    }


def _render_trial(st, name: str, config: dict, trial: dict, predictions: dict, locks: dict, enabled: bool) -> None:
    title = config["title"]
    locked_at = str(locks.get(name, ""))
    complete = _trial_after_lock(trial, locked_at)
    with st.expander(f"{title}: {'complete' if complete else 'not complete'}", expanded=enabled and not complete):
        if not enabled:
            st.info("Complete the preceding trial first.")
            return
        st.write(config["teaching"])
        left, right, third = st.columns(3)
        left.metric("Forward speed", f"{config['linear_x']:.2f} m/s")
        right.metric("Turning speed", f"{config['angular_z']:.2f} rad/s")
        third.metric("Command time", f"{config['duration']:.1f} s")
        _motion_preview(st, config["linear_x"], config["angular_z"], config["duration"], "Predicted path preview")

        predictions[name] = st.text_area(
            config["prompt"],
            value=str(predictions.get(name, "")),
            disabled=bool(locked_at),
            key=f"mission2.prediction.{name}",
            height=85,
        )
        if not locked_at:
            if st.button(
                "Save this prediction",
                key=f"mission2.lock.{name}",
                disabled=len(str(predictions[name]).strip()) < 30,
            ):
                locks[name] = datetime.now(timezone.utc).isoformat()
                set_response(st, "mission_2.predictions", predictions)
                set_response(st, "mission_2.prediction_locks", locks)
                st.rerun()
            st.caption("Write at least one complete sentence before saving the prediction.")
            return

        st.success("Prediction saved. The Run button is now available.")
        st.write("Run starts by returning the simulated world to its initial position. It then sends the displayed command and finishes with a stop command.")
        if st.button(f"Run {title.lower()}", type="primary", key=f"mission2.run.{name}"):
            with st.spinner("Resetting the simulator, moving the robot, and recording evidence..."):
                succeeded, message = _run_trial(name, config["linear_x"], config["angular_z"], config["duration"])
            st.session_state[f"mission2.status.{name}"] = (succeeded, message)
            st.rerun()

        status = st.session_state.get(f"mission2.status.{name}")
        if status:
            (st.success if status[0] else st.error)(status[1])
        if complete:
            st.success("A completed trial and stop command were recorded after this prediction.")
            st.dataframe([_result_row(name, trial)], hide_index=True, width="stretch")
        if st.button("Revise prediction and rerun", key=f"mission2.revise.{name}"):
            locks.pop(name, None)
            st.session_state.pop(f"mission2.status.{name}", None)
            set_response(st, "mission_2.prediction_locks", locks)
            st.rerun()


def render(st) -> None:
    st.title("Mission 2: See how velocity commands create motion")
    st.write(
        "You will learn what the two driving values mean, predict one motion at a time, run the robot, "
        "and compare your prediction with measurements."
    )

    st.subheader("Step 1: Learn the motion vocabulary")
    st.markdown(
        "- **Velocity** describes how the robot should move now. It does not name a destination.\n"
        "- **`linear.x`** is forward or backward speed in meters per second. Positive values move forward.\n"
        "- **`angular.z`** is turning speed in radians per second. Positive values turn left and negative values turn right.\n"
        "- **Duration** is how long the command is repeated. A longer duration usually produces more movement.\n"
        "- A **Twist message** holds these driving values. This lab uses only `linear.x` and `angular.z`."
    )
    st.info("Straight: forward speed only   |   Rotate: turning speed only   |   Curve: both speeds together")
    columns = st.columns(3)
    for column, config in zip(columns, FIXED_TRIALS.values()):
        with column:
            _motion_preview(st, config["linear_x"], config["angular_z"], config["duration"], config["title"])

    st.subheader("Step 2: Run three guided trials")
    st.write(
        "Work from top to bottom. For each trial, write and save a prediction, then use the Run button. "
        "The next trial opens after evidence from the current one has been recorded."
    )
    trials = [trial for trial in motion_trials() if str(trial.get("trial_type", "")) in TRIAL_TYPES]
    by_type = {str(trial.get("trial_type")): trial for trial in trials}
    predictions = dict(response(st, "mission_2.predictions", {}))
    locks = dict(response(st, "mission_2.prediction_locks", {}))

    previous_complete = True
    for name, config in FIXED_TRIALS.items():
        _render_trial(st, name, config, by_type.get(name, {}), predictions, locks, previous_complete)
        previous_complete = previous_complete and _trial_after_lock(by_type.get(name, {}), str(locks.get(name, "")))
    set_response(st, "mission_2.predictions", predictions)
    set_response(st, "mission_2.prediction_locks", locks)

    st.subheader("Step 3: Design and run a different curve")
    if not previous_complete:
        st.info("Complete the three guided trials before designing the modified curve.")
    else:
        modified_locked = bool(locks.get("curve_modified"))
        stored_settings = dict(response(st, "mission_2.modified_settings", {}))
        linear_x = st.slider(
            "Forward speed in meters per second",
            0.05,
            0.22,
            float(stored_settings.get("linear_x", 0.12)),
            0.01,
            disabled=modified_locked,
        )
        angular_z = st.slider(
            "Turning speed in radians per second",
            -0.8,
            0.8,
            float(stored_settings.get("angular_z", 0.6)),
            0.1,
            disabled=modified_locked,
        )
        duration = 4.0
        settings = {"linear_x": linear_x, "angular_z": angular_z, "duration": duration}
        set_response(st, "mission_2.modified_settings", settings)
        if abs(angular_z) < 0.1:
            st.warning("Choose a nonzero turning speed so this trial produces a curve.")
        else:
            direction = "left" if angular_z > 0 else "right"
            radius = abs(linear_x / angular_z)
            st.info(f"Prediction aid: this command turns {direction}. Its approximate turn radius is {radius:.2f} m. A smaller radius means a tighter curve.")
        modified_config = {
            "title": "Modified curve",
            "linear_x": linear_x,
            "angular_z": angular_z,
            "duration": duration,
            "teaching": "Use the preview and the direction and radius explanation to predict how this curve differs from the first curve.",
            "prompt": "How will this path differ from the first curved trial? Sentence starter: This curve should be tighter, wider, or turn the other way because...",
        }
        if abs(angular_z) >= 0.1:
            _render_trial(st, "curve_modified", modified_config, by_type.get("curve_modified", {}), predictions, locks, True)
            set_response(st, "mission_2.predictions", predictions)
            set_response(st, "mission_2.prediction_locks", locks)

    st.subheader("Step 4: Read the measurements")
    valid_rows = [_result_row(name, by_type[name]) for name in TRIAL_TYPES if name in by_type and by_type[name].get("completed")]
    if valid_rows:
        st.dataframe(valid_rows, hide_index=True, width="stretch")
    else:
        st.info("Measurements will appear here after the first trial.")
    st.markdown(
        "- **Commanded path length** is forward speed multiplied by command time. For a curve, this is distance along the arc.\n"
        "- **Estimated traveled path** adds the small movements reported by odometry.\n"
        "- **Start-to-end distance** is the straight line between the starting and ending positions. It is shorter than the arc for a curved path.\n"
        "- **Direction change** reports how much the robot turned, in degrees.\n"
        "- Small differences are expected because command timing, simulation updates, and measured motion are not perfectly identical."
    )
    if st.button("Refresh measurements"):
        st.rerun()

    completed_trials = sum(_trial_after_lock(by_type.get(name, {}), str(locks.get(name, ""))) for name in TRIAL_TYPES)
    st.progress(completed_trials / len(TRIAL_TYPES), text=f"Motion trials: {completed_trials} of {len(TRIAL_TYPES)} complete")
    if completed_trials < len(TRIAL_TYPES):
        next_name = next(name for name in TRIAL_TYPES if not _trial_after_lock(by_type.get(name, {}), str(locks.get(name, ""))))
        st.info("Next action: complete " + next_name.replace("_", " ") + ".")

    st.subheader("Step 5: Explain the evidence")
    st.write("Use the completed table and the explanations directly above it. Each response should be at least two complete sentences.")
    text_response(
        st,
        "mission_2.motion_comparison",
        "Choose one trial. How did the measured motion compare with your prediction? Cite at least two values from the table.",
        height=110,
    )
    text_response(
        st,
        "mission_2.measurement_explanation",
        "For one curved trial, explain why estimated traveled path and start-to-end distance describe different measurements.",
        height=110,
    )
    st.markdown(
        "**Three ways the system stops unwanted motion**\n\n"
        "- **Command guard:** checks every proposed driving command before it reaches the robot. It limits speeds that are too large and rejects invalid values.\n"
        "- **Final zero command:** marks the planned end of a trial by commanding zero forward speed and zero turning speed.\n"
        "- **Stale-command timeout:** acts as a backup. If a program crashes or communication stops while the robot is moving, the guard sends a stop command after 0.5 seconds without a new command."
    )
    text_response(
        st,
        "mission_2.safety_explanation",
        "Explain the three protections in your own words. Complete these sentences: The command guard checks... The final zero command... The timeout is needed if...",
        height=110,
    )

    responses = st.session_state.get("responses", {})
    check = evaluate(trials, responses)
    render_check(st, check)
    current_id = evidence_id(trials, mission_responses(responses))
    checked_id = st.session_state.get("checked_evidence_ids", {}).get("mission_2")
    if check.passed and checked_id != current_id:
        if st.button("Check and save Mission 2", type="primary"):
            reset_ok, reset_message = _reset_robot()
            st.session_state["mission2.final_reset"] = (reset_ok, reset_message)
            if reset_ok:
                evidence = {"evidence_id": current_id, "trials": trials, "check": [item.__dict__ for item in check.requirements]}
                save_mission("mission_2", evidence, responses)
                complete_mission(st, "mission_2", current_id)
            st.rerun()
    final_reset = st.session_state.get("mission2.final_reset")
    if final_reset:
        (st.success if final_reset[0] else st.error)(final_reset[1])
    if check.passed and checked_id == current_id:
        st.success("Mission 2 is saved.")
        if st.button("Continue to Mission 3", type="primary"):
            reset_ok, reset_message = _reset_robot()
            st.session_state["mission2.final_reset"] = (reset_ok, reset_message)
            if reset_ok:
                set_stage(st, "mission_3")
            else:
                st.rerun()
