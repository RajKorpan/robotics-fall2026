from __future__ import annotations

from pathlib import Path

from lab.evidence import behavior_evaluation, evidence_id, latest_graph
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission, snapshot_student_source
from lab.ui import choice_response, render_check, text_response
from missions.mission_3 import evaluate


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "ros2_ws" / "src" / "week01_behavior"


def render(st) -> None:
    st.title("Mission 3: Write a sensor-based behavior")
    st.write("Create a ROS node that moves slowly when the path is clear and stops safely before an obstacle.")
    st.warning("Publish only to /student_cmd_vel. The supplied guard is the only component that publishes to /cmd_vel.")

    st.subheader("Design before coding")
    design = dict(response(st, "mission_3.design", {}))
    col1, col2, col3 = st.columns(3)
    with col1:
        design["front_width"] = st.number_input("Front half-width (degrees)", 5, 45, int(design.get("front_width", 15)))
        design["stop_distance"] = st.number_input("Stop distance (m)", 0.2, 1.5, float(design.get("stop_distance", 0.5)), 0.05)
    with col2:
        design["forward_speed"] = st.number_input("Forward speed (m/s)", 0.02, 0.18, float(design.get("forward_speed", 0.08)), 0.01)
        design["invalid_policy"] = st.selectbox("No valid ranges", ["Stop", "Continue", "Use last value"], index=0)
    with col3:
        design["stale_policy"] = st.selectbox("Scan becomes stale", ["Stop", "Continue", "Use last value"], index=0)
        design["resume_policy"] = st.selectbox("Obstacle is removed", ["Resume after a valid clear scan", "Remain stopped"], index=0)
    set_response(st, "mission_3.design", design)

    st.subheader("Implement and test")
    st.code(
        "ros2_ws/src/week01_behavior/week01_behavior/decision.py\n"
        "ros2_ws/src/week01_behavior/week01_behavior/obstacle_guard.py\n"
        "ros2_ws/src/week01_behavior/test/test_decision.py"
    )
    st.code(
        "cd ros2_ws\n"
        "colcon build --packages-select week01_behavior\n"
        "source install/setup.bash\n"
        "colcon test --packages-select week01_behavior\n"
        "colcon test-result --verbose\n"
        "bash ../scripts/evaluate_behavior.sh",
        language="bash",
    )
    st.markdown(
        "The evaluator checks clear path, outside threshold, inside threshold, invalid scan, "
        "stale scan, and velocity bounds. Then launch your node and inspect it with `ros2 node info /obstacle_guard`."
    )
    behavior = behavior_evaluation()
    if behavior:
        scenario_rows = [
            {"Scenario": name, **result}
            for name, result in behavior.get("scenarios", {}).items()
        ]
        st.dataframe(scenario_rows, hide_index=True, width="stretch")
    else:
        st.warning("No behavior evaluation evidence found.")
    if st.button("Refresh behavior evidence"):
        st.rerun()

    st.subheader("Investigate one failure")
    text_response(
        st,
        "mission_3.failure_investigation",
        "Temporarily introduce one safe failure (wrong comparison, narrow sector, bad invalid-data policy, or missing timeout). Predict, test, restore, and explain the result.",
        height=150,
    )
    st.subheader("Explain the completed system")
    choice_response(
        st,
        "mission_3.architecture",
        "The implemented stimulus–threshold–response behavior is primarily which architecture?",
        ["Reactive", "Behavior-based", "Deliberative", "Hybrid"],
    )
    text_response(st, "mission_3.decision_node", "Which node now makes the move/stop decision?")
    text_response(st, "mission_3.received_information", "What information does that node receive?")
    text_response(st, "mission_3.scan_assumptions", "What assumptions does it make about /scan?")
    text_response(st, "mission_3.missing_vs_clear", "Why is no sensor data different from no obstacle?")
    text_response(st, "mission_3.hardware_limitation", "What limitation matters before using this behavior on hardware?")
    text_response(st, "mission_3.whole_system", "Which components together produce the final behavior?")
    text_response(st, "mission_3.reactive_tradeoff", "Why is this reactive behavior fast, and what memory, prediction, or long-term capability does it lack?")
    text_response(st, "mission_3.behavior_arbitration", "If obstacle avoidance, wandering, and goal following all publish candidate motions, what conflict must an arbitrator resolve?")
    text_response(st, "mission_3.hybrid_extension", "Where could a world model and planner be added to make a future system hybrid without removing fast obstacle stopping?")
    text_response(st, "mission_3.safety_authority", "Why must the supplied command guard be able to restrict commands from teleoperation or your behavior node?")
    text_response(st, "mission_3.software_vs_estop", "Why are velocity limits and stale-command stopping not a substitute for a physical emergency stop on hardware?")

    graph = latest_graph()
    check = evaluate(behavior, graph, st.session_state.get("responses", {}), SOURCE_ROOT)
    render_check(st, check)
    current_id = evidence_id(behavior, design, graph.get("captured_at"))
    checked_id = st.session_state.get("checked_evidence_ids", {}).get("mission_3")
    if check.passed and checked_id != current_id:
        if st.button("Check and save Mission 3", type="primary"):
            evidence = {"evidence_id": current_id, "behavior": behavior, "check": [item.__dict__ for item in check.requirements]}
            save_mission("mission_3", evidence, st.session_state.get("responses", {}))
            snapshot_student_source()
            complete_mission(st, "mission_3", current_id)
            st.rerun()
    if checked_id == current_id:
        st.success("Your tested behavior and source snapshot are saved.")
        if st.button("Continue to final submission", type="primary"):
            set_stage(st, "final")
