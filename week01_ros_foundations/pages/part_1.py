from __future__ import annotations

from lab.navigation import set_stage
from lab.session import response, set_response
from lab.ui import choice_response, text_response


def render(st) -> None:
    st.title("Part 1: Why robotics software is difficult")
    st.write(
        "Robots connect software to a changing physical world. Their software must interpret "
        "imperfect sensors, respond on time, coordinate concurrent programs, and remain safe "
        "when hardware or communication fails."
    )

    st.subheader("Opening analysis")
    st.caption("Compare a robot with an ordinary application before using ROS 2 terminology.")
    challenge_one = text_response(
        st,
        "part_1.challenge_one",
        "Describe one challenge that is especially important because a robot acts in the physical world.",
    )
    challenge_two = text_response(
        st,
        "part_1.challenge_two",
        "Describe a second robotics-software challenge that differs from the first.",
    )
    consequence = text_response(
        st,
        "part_1.failure_consequence",
        "Give one concrete consequence of incorrect sensor data or a late software response.",
    )

    st.subheader("Four recurring sources of difficulty")
    st.markdown(
        "- **Sensors:** different formats, rates, fields of view, uncertainty, and failure modes.\n"
        "- **Timing:** a delay changes what happens in the physical world.\n"
        "- **Distribution:** multiple programs run concurrently and communicate.\n"
        "- **Hardware:** wheels slip, sensors saturate, batteries drain, and models are imperfect."
    )
    sensor_response = choice_response(
        st,
        "part_1.sensor_response",
        "A range sensor stops publishing. What is the safest interpretation for a move/stop behavior?",
        [
            "The path is clear because no obstacle was reported",
            "The state is unknown, so stop and report missing data",
            "Continue forever using the last measurement",
        ],
    )
    distributed_failure = text_response(
        st,
        "part_1.distributed_failure",
        "A visualization still runs, but the robot no longer moves. Name two different components or communication paths you would inspect and explain why.",
        height=130,
    )

    st.subheader("Timing explorer")
    delay_options = [0.10, 0.25, 0.50, 0.75, 1.00]
    prior_speed = float(response(st, "part_1.delay_speed", 0.20))
    prior_delay = float(response(st, "part_1.delay_seconds", 0.50))
    col1, col2 = st.columns(2)
    with col1:
        speed = st.number_input(
            "Robot speed (m/s)", 0.05, 1.00, prior_speed, 0.05,
            key="widget.part_1.delay_speed",
        )
    with col2:
        delay = st.select_slider(
            "Response delay (seconds)",
            options=delay_options,
            value=prior_delay if prior_delay in delay_options else 0.50,
            key="widget.part_1.delay_seconds",
        )
    set_response(st, "part_1.delay_speed", speed)
    set_response(st, "part_1.delay_seconds", delay)
    extra_distance = speed * delay
    set_response(st, "part_1.delay_distance", round(extra_distance, 3))
    st.metric("Distance traveled before the delayed response", f"{extra_distance:.3f} m")
    timing_explanation = text_response(
        st,
        "part_1.timing_explanation",
        "Explain why the same delay could be merely inconvenient in one program but dangerous in a robot.",
    )

    correct_sensor_response = sensor_response == "The state is unknown, so stop and report missing data"
    complete = all(
        len(value.strip()) >= 40
        for value in (challenge_one, challenge_two, consequence, distributed_failure, timing_explanation)
    )
    if sensor_response and not correct_sensor_response:
        st.warning("Missing sensor data is uncertainty—not evidence that the path is clear. Reconsider the policy.")
    if not complete:
        st.info("Give a specific explanation of at least 40 characters for each written response.")
    if st.button("Continue to Part 2", type="primary", disabled=not (complete and correct_sensor_response)):
        set_stage(st, "part_2")
