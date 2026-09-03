from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from lab.evidence import behavior_evaluation, evidence_id, latest_graph
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission, snapshot_student_source
from lab.ui import render_check, text_response
from missions.mission_3 import EXPLANATION_KEYS, evaluate


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "ros2_ws" / "src" / "week01_behavior"
DECISION_FILE = SOURCE_ROOT / "week01_behavior" / "decision.py"
STUDENT_TEST_FILE = SOURCE_ROOT / "test" / "test_student_decision.py"


def _run(command: str, timeout: float = 90.0) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["bash", "-lc", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"The command could not finish: {error}"
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return result.returncode == 0, output or "Command completed."


def _source_state() -> dict[str, str]:
    state = {}
    for path in (DECISION_FILE, STUDENT_TEST_FILE):
        if path.exists():
            state[str(path.relative_to(SOURCE_ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            state[str(path.relative_to(SOURCE_ROOT))] = "missing"
    return state


def _stable_behavior(behavior: dict) -> dict:
    return {
        "unit_tests_passed": bool(behavior.get("unit_tests_passed")),
        "command_bounded": bool(behavior.get("command_bounded")),
        "ros_node_verified": bool(behavior.get("ros_node_verified")),
        "scenarios": behavior.get("scenarios", {}),
    }


def _result_message(st, key: str) -> None:
    result = st.session_state.get(key)
    if not result:
        return
    passed, output = result
    if passed:
        st.success("The check passed.")
    else:
        st.error("The check did not pass yet. Read the final lines below, revise your code, save it, and run the check again.")
    st.code(output[-5000:], language="text")


def _pipeline(st) -> None:
    st.html(
        """
        <div style="display:flex;align-items:stretch;gap:8px;flex-wrap:wrap;margin:10px 0 18px 0">
          <div style="flex:1;min-width:155px;padding:14px;border-radius:10px;background:#e0f2fe;border:1px solid #7dd3fc">
            <b>1. LiDAR sensor</b><br><span style="font-size:0.92rem">Sends a list of distances on <code>/scan</code></span>
          </div>
          <div style="align-self:center;font-size:1.5rem">→</div>
          <div style="flex:1;min-width:155px;padding:14px;border-radius:10px;background:#fef3c7;border:1px solid #fbbf24">
            <b>2. Your first function</b><br><span style="font-size:0.92rem"><code>front_distance()</code> finds the nearest valid distance ahead</span>
          </div>
          <div style="align-self:center;font-size:1.5rem">→</div>
          <div style="flex:1;min-width:155px;padding:14px;border-radius:10px;background:#ede9fe;border:1px solid #a78bfa">
            <b>3. Your second function</b><br><span style="font-size:0.92rem"><code>decide_velocity()</code> chooses move or stop</span>
          </div>
          <div style="align-self:center;font-size:1.5rem">→</div>
          <div style="flex:1;min-width:155px;padding:14px;border-radius:10px;background:#dcfce7;border:1px solid #86efac">
            <b>4. Supplied ROS node</b><br><span style="font-size:0.92rem">Publishes the choice on <code>/student_cmd_vel</code></span>
          </div>
        </div>
        """
    )


def render(st) -> None:
    st.title("Mission 3: Program the robot to stop for an obstacle")
    st.write(
        "You will write and test the decision-making code for a small reactive behavior. The robot will "
        "move slowly while the space ahead is clear and stop when an obstacle is too close or the sensor "
        "cannot provide a usable measurement."
    )
    _pipeline(st)

    st.subheader("What you will write and what is already supplied")
    left, right = st.columns(2)
    with left:
        st.markdown(
            "**You will write**\n\n"
            "- `front_distance()`, which turns many LiDAR readings into one useful distance\n"
            "- `decide_velocity()`, which turns that distance into a forward speed\n"
            "- one unit test in a new test file"
        )
    with right:
        st.markdown(
            "**The lab supplies**\n\n"
            "- the ROS 2 node and its connection to `/scan`\n"
            "- publication to `/student_cmd_vel`\n"
            "- a watchdog that stops if scans stop arriving\n"
            "- additional tests and a command guard"
        )
    st.warning("Your code proposes motion only on `/student_cmd_vel`. Do not publish directly to `/cmd_vel`.")

    st.subheader("Step 1 of 7: Open the file you will edit")
    st.write(
        "The repository on your computer and `/workspace` inside Docker are the same shared files. "
        "The recommended method is to open the cloned repository in VS Code or another text editor on "
        "your computer. Then open this file:"
    )
    st.code("week01_ros_foundations/ros2_ws/src/week01_behavior/week01_behavior/decision.py", language="text")
    if shutil.which("nano"):
        st.write("You can instead edit inside the browser desktop terminal:")
        st.code(
            "cd /workspace/week01_ros_foundations\n"
            "nano ros2_ws/src/week01_behavior/week01_behavior/decision.py",
            language="bash",
        )
        st.caption("In nano, save with Ctrl+O, press Enter, then exit with Ctrl+X.")
    st.write(
        "The file contains two unfinished functions marked by `NotImplementedError`. Edit only those two "
        "functions. Leave `obstacle_guard.py` unchanged."
    )

    st.subheader("Step 2 of 7: Understand one LiDAR scan")
    st.write(
        "LiDAR measures distance by sending light in many directions. ROS stores one sweep as a list named "
        "`ranges`. Each list position has an angle. An angle of 0 radians points straight ahead. Negative "
        "angles are to one side and positive angles are to the other side."
    )
    st.code(
        "ranges:          [0.10,  inf, 0.80,  nan, 0.60,  inf, 0.10]\n"
        "index:              0     1     2     3     4     5     6\n"
        "angle (radians): -0.30 -0.20 -0.10  0.00  0.10  0.20  0.30\n"
        "                                      front",
        language="text",
    )
    st.markdown(
        "For this example, `angle_min` is `-0.30` and `angle_increment` is `0.10`. Therefore:\n\n"
        "`angle = angle_min + index × angle_increment`\n\n"
        "If the front half-width is `0.15`, only angles from `-0.15` through `0.15` count as ahead. "
        "That selects `0.80`, `nan`, and `0.60`. `nan` means the sensor has no usable number there, so "
        "ignore it. The nearest valid front reading is therefore `0.60` meters."
    )

    st.subheader("Step 3 of 7: Implement `front_distance()`")
    st.write("Inside the first function, implement these operations in this order:")
    st.markdown(
        "1. Create an empty list for valid front distances.\n"
        "2. Use `enumerate(ranges)` to get each reading and its index.\n"
        "3. Calculate the angle for that index.\n"
        "4. Keep the reading only when `abs(angle) <= half_width_radians`, the value is finite, and it is greater than zero.\n"
        "5. If the list is empty, return `None`.\n"
        "6. Otherwise, return the smallest value in the list."
    )
    st.write("Add `import math` near the top of the file. These Python tools provide the pieces you need:")
    st.code(
        "for index, distance in enumerate(ranges):\n"
        "    angle = angle_min + index * angle_increment\n"
        "    in_front = abs(angle) <= half_width_radians\n"
        "    is_valid = math.isfinite(distance) and distance > 0\n\n"
        "min(valid_distances)",
        language="python",
    )
    if st.button("Run the front-distance checks", key="mission3.front_check"):
        command = (
            "source /opt/ros/jazzy/setup.bash && "
            "cd /workspace/week01_ros_foundations/ros2_ws/src/week01_behavior && "
            "python3 test/test_decision.py "
            "DecisionTests.test_front_sector_ignores_invalid_values "
            "DecisionTests.test_empty_front_sector_is_missing"
        )
        st.session_state["mission3.front_result"] = _run(command, 30.0)
    _result_message(st, "mission3.front_result")

    st.subheader("Step 4 of 7: Implement `decide_velocity()`")
    st.write(
        "The second function receives the nearest front distance. It returns only a number representing "
        "forward speed. A return value of `0.0` means stop."
    )
    st.table(
        [
            {"Input condition": "distance is None", "Meaning": "No usable front measurement", "Return": "0.0"},
            {"Input condition": "distance <= stop_distance", "Meaning": "Obstacle is at or inside the limit", "Return": "0.0"},
            {"Input condition": "distance > stop_distance", "Meaning": "Measured space ahead is clear", "Return": "forward_speed, limited to 0.18"},
        ]
    )
    st.write(
        "Use `if` statements for the first two rows. For the final row, bound the requested speed so the "
        "function never returns less than 0 or more than 0.18 meters per second."
    )
    st.code("max(0.0, min(float(forward_speed), 0.18))", language="python")
    if st.button("Run the move-or-stop checks", key="mission3.decision_check"):
        command = (
            "source /opt/ros/jazzy/setup.bash && "
            "cd /workspace/week01_ros_foundations/ros2_ws/src/week01_behavior && "
            "python3 test/test_decision.py"
        )
        st.session_state["mission3.decision_result"] = _run(command, 30.0)
    _result_message(st, "mission3.decision_result")

    st.subheader("Step 5 of 7: Create one test of your own")
    st.write(
        "A unit test calls one small piece of code with a known input and checks the output. Create the "
        "file below in your computer's editor, or use the terminal command to create and open it."
    )
    st.code("week01_ros_foundations/ros2_ws/src/week01_behavior/test/test_student_decision.py", language="text")
    if shutil.which("nano"):
        st.code(
            "cd /workspace/week01_ros_foundations\n"
            "touch ros2_ws/src/week01_behavior/test/test_student_decision.py\n"
            "nano ros2_ws/src/week01_behavior/test/test_student_decision.py",
            language="bash",
        )
    st.write("Enter this test. It checks the exact boundary where the robot must stop.")
    st.code(
        "import unittest\n\n"
        "from week01_behavior.decision import decide_velocity\n\n\n"
        "class StudentDecisionTest(unittest.TestCase):\n"
        "    def test_robot_stops_at_boundary(self):\n"
        "        speed = decide_velocity(0.5, 0.5, 0.08)\n"
        "        self.assertEqual(speed, 0.0)\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    unittest.main()",
        language="python",
    )
    st.write(
        "Save the file. In this test, the measured distance and stop distance are both 0.5 meters. "
        "Stopping at the boundary gives the robot a conservative rule."
    )

    st.subheader("Step 6 of 7: Build and run your ROS 2 node")
    st.write(
        "Keep the TurtleBot simulation from Mission 1 running. Open a second terminal in the browser "
        "desktop and run each command below one at a time."
    )
    st.code(
        "cd /workspace/week01_ros_foundations/ros2_ws\n"
        "colcon build --packages-select week01_behavior --symlink-install\n"
        "source install/setup.bash\n"
        "ros2 run week01_behavior obstacle_guard",
        language="bash",
    )
    st.write(
        "Leave the last command running. The node receives `/scan`, calls your two functions, and publishes "
        "the result to `/student_cmd_vel`. Watch Gazebo. The robot should move slowly when clear and stop "
        "before an obstacle. Press Ctrl+C in that terminal when you need to stop the node."
    )
    with st.expander("If the terminal says that a command or package is not found"):
        st.code(
            "source /opt/ros/jazzy/setup.bash\n"
            "source /workspace/week01_ros_foundations/ros2_ws/install/setup.bash\n"
            "export ROS_DOMAIN_ID=24",
            language="bash",
        )

    st.markdown("**Verify that ROS 2 can see your running node**")
    st.write("While `obstacle_guard` is still running, open a third terminal and run:")
    st.code(
        "ros2 node list | grep obstacle_guard\n"
        "ros2 node info /obstacle_guard",
        language="bash",
    )
    st.write(
        "The first command should print `/obstacle_guard`. In the second command's output, find `/scan` "
        "under subscribers and `/student_cmd_vel` under publishers. Wait a few seconds, then return here."
    )

    st.subheader("Step 7 of 7: Run the complete evaluation")
    st.write(
        "This check builds the package, runs the supplied tests and your test, evaluates five sensor "
        "situations, and records whether the running ROS node was visible. Keep the node running while "
        "you click the button."
    )
    if st.button("Build, test, and evaluate my behavior", type="primary", key="mission3.evaluate"):
        st.session_state["mission3.evaluation_result"] = _run(
            "cd /workspace/week01_ros_foundations && bash scripts/evaluate_behavior.sh",
            120.0,
        )
        st.rerun()
    _result_message(st, "mission3.evaluation_result")

    behavior = behavior_evaluation()
    if behavior:
        labels = {
            "clear_path": "Clear path: move slowly",
            "outside_threshold": "Obstacle beyond limit: move slowly",
            "inside_threshold": "Obstacle too close: stop",
            "invalid_scan": "No valid distances: stop",
            "stale_scan": "Sensor data unavailable: stop",
        }
        scenario_rows = []
        for name, result in behavior.get("scenarios", {}).items():
            scenario_rows.append(
                {
                    "Situation": labels.get(name, name.replace("_", " ").title()),
                    "Your output": result.get("actual"),
                    "Expected output": result.get("expected"),
                    "Result": "Pass" if result.get("passed") else "Revise and retry",
                }
            )
        st.dataframe(scenario_rows, hide_index=True, width="stretch")
        if behavior.get("ros_node_verified"):
            st.success("The evaluator also found `/obstacle_guard` in the live ROS 2 graph.")
        else:
            st.warning(
                "The evaluator did not find `/obstacle_guard`. Start the node as shown in Step 6, leave it "
                "running for a few seconds, and run the complete evaluation again."
            )
    else:
        st.info("No evaluation has been recorded yet. Complete the steps above, then run the evaluation.")

    st.subheader("Explain what you built")
    text_response(
        st,
        "mission_3.data_to_command",
        "How do your two functions turn a list of LiDAR distances into a move-or-stop command?",
        help="Describe what each function receives, decides, and returns.",
        height=110,
    )
    text_response(
        st,
        "mission_3.missing_data_safety",
        "Why does the robot stop when there is no valid front measurement instead of treating the path as clear?",
        help="Think about what the robot knows and does not know when measurements are missing or invalid.",
        height=110,
    )
    text_response(
        st,
        "mission_3.system_layers",
        "How do your decision functions, the supplied ROS node, and the command guard work together?",
        help="Follow the information from /scan to /student_cmd_vel and then to /cmd_vel.",
        height=110,
    )

    graph = latest_graph()
    responses = st.session_state.get("responses", {})
    check = evaluate(behavior, graph, responses, SOURCE_ROOT)
    completed_requirements = sum(item.passed for item in check.requirements)
    st.subheader("Mission 3 progress")
    st.progress(completed_requirements / len(check.requirements))
    st.write(f"{completed_requirements} of {len(check.requirements)} requirements complete")
    remaining = [item.label for item in check.requirements if not item.passed]
    if remaining:
        st.info(f"Next requirement to complete: {remaining[0]}")
    render_check(st, check)
    response_payload = {key: responses.get(f"mission_3.{key}", "") for key in EXPLANATION_KEYS}
    current_id = evidence_id(_stable_behavior(behavior), _source_state(), response_payload)
    checked_id = st.session_state.get("checked_evidence_ids", {}).get("mission_3")
    if check.passed and checked_id != current_id:
        if st.button("Check and save Mission 3", type="primary"):
            evidence = {
                "evidence_id": current_id,
                "behavior": behavior,
                "source": _source_state(),
                "check": [item.__dict__ for item in check.requirements],
            }
            save_mission("mission_3", evidence, responses)
            snapshot_student_source()
            complete_mission(st, "mission_3", current_id)
            st.rerun()
    if check.passed and checked_id == current_id:
        st.success("Your tested behavior, explanations, and source files are saved.")
        if st.button("Continue to final submission", type="primary"):
            set_stage(st, "final")
