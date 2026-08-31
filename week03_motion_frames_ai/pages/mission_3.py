from __future__ import annotations

from pathlib import Path

from lab.ai_log import assigned_pattern, load_lock, lock_original, write_diff
from lab.evidence import ai_evaluation, evidence_id
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission, snapshot_pattern_source
from lab.ui import render_check, text_response
from missions.mission_3 import evaluate


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "ros2_ws" / "src" / "week03_pattern"
FINAL_SOURCE = SOURCE_ROOT / "week03_pattern" / "pattern.py"


PATTERN_REQUIREMENTS = {
    "rounded_rectangle": "Drive a closed rounded rectangle using alternating straight segments and quarter-turn arcs.",
    "l_path": "Drive an L-shaped path with two straight legs and one 90-degree turn, then stop.",
    "alternating_arcs": "Drive at least four alternating left and right arcs, then stop near the original heading.",
}


def render(st) -> None:
    st.title("Mission 3: AI-assisted ROS development")
    course_id = str(st.session_state.get("student", {}).get("course_id", ""))
    pattern = assigned_pattern(course_id)
    specification = PATTERN_REQUIREMENTS[pattern]
    st.info(f"Your assigned pattern: **{pattern.replace('_', ' ').title()}**")
    st.write(specification)
    st.warning("Do not run AI-generated robot code until you have inspected it and designed tests.")

    lock = load_lock()
    if not lock:
        st.subheader("1. Specify and preserve the original AI interaction")
        spec = text_response(
            st,
            "mission_3.specification",
            "Write a precise specification including inputs, outputs, coordinate conventions, velocity limits, stopping behavior, and test expectations.",
            height=170,
        )
        prompt = text_response(st, "mission_3.original_prompt", "Paste the exact prompt you sent to the AI assistant.", height=170)
        output = text_response(st, "mission_3.original_output", "Paste the complete original AI output without editing it.", height=260)
        if st.button(
            "Lock original prompt and output",
            type="primary",
            disabled=len(spec.strip()) < 150 or len(prompt.strip()) < 80 or len(output.strip()) < 150,
        ):
            metadata = lock_original(course_id, spec, prompt, output)
            set_response(st, "mission_3.ai_locked_at", metadata["locked_at"])
            st.rerun()
        st.caption("Locking is permanent for this submission directory so later changes remain auditable.")
        return

    st.success(f"Original AI interaction locked at {lock.get('locked_at')}.")
    st.code(str(ROOT / "student_submission" / "mission_3" / "ai"))
    st.subheader("2. Review assumptions and design tests")
    text_response(st, "mission_3.assumptions", "What undocumented assumptions did the AI make about APIs, frames, timing, or the robot?")
    text_response(st, "mission_3.problems", "Identify errors, omissions, unsafe behavior, or claims that require verification.")
    st.markdown(
        "Required tests include zero/empty pattern, segment order, velocity limits, stop after completion, "
        "stop on interruption, heading wraparound, and one Gazebo integration run."
    )
    st.code(
        "ros2_ws/src/week03_pattern/week03_pattern/pattern.py\n"
        "ros2_ws/src/week03_pattern/week03_pattern/pattern_node.py\n"
        "ros2_ws/src/week03_pattern/test/test_pattern.py"
    )
    st.subheader("3. Modify, test, and evaluate")
    st.code(
        "cd ros2_ws\n"
        "colcon build --packages-select week03_pattern --symlink-install\n"
        "source install/setup.bash\n"
        "colcon test --packages-select week03_pattern\n"
        "colcon test-result --verbose\n"
        "bash ../scripts/evaluate_ai_pattern.sh",
        language="bash",
    )
    result = ai_evaluation()
    if result:
        st.json({key: value for key, value in result.items() if key != "unit_test_output"})
        with st.expander("Test output"):
            st.code(result.get("unit_test_output", ""))
    else:
        st.warning("No AI-pattern evaluation evidence found.")
    if st.button("Refresh evaluation"):
        st.rerun()

    text_response(st, "mission_3.modifications", "What did you change after reviewing the AI output, and why?")
    text_response(st, "mission_3.test_argument", "Why do your tests establish the required behavior? State what each important test rules out.", height=150)
    text_response(st, "mission_3.remaining_limits", "What does your evidence not establish, and what remains risky?")
    text_response(st, "mission_3.ai_disclosure", "Write your individual AI usage disclosure, including tool, purpose, verification, and responsibility.")

    check = evaluate(result, lock, st.session_state.get("responses", {}), SOURCE_ROOT)
    render_check(st, check)
    current_id = evidence_id(result, lock)
    checked = st.session_state.get("checked_evidence_ids", {}).get("mission_3")
    if check.passed and checked != current_id and st.button("Check and save Mission 3", type="primary"):
        save_mission("mission_3", {"evidence_id": current_id, "ai_evaluation": result, "ai_lock": lock, "check": [item.__dict__ for item in check.requirements]}, st.session_state.get("responses", {}))
        snapshot_pattern_source()
        write_diff(FINAL_SOURCE)
        complete_mission(st, "mission_3", current_id)
        st.rerun()
    if checked == current_id:
        st.success("The original output, final code, diff, tests, and explanations are saved.")
        if st.button("Continue to final submission", type="primary"):
            set_stage(st, "final")
