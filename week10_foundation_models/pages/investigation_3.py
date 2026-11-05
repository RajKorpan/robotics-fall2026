"""Three prompt comparisons followed by a required student-written robot prompt."""
from lab.local_config import MODEL_CONFIG
from lab.local_jobs import installed, start_job, job_status, cancel_job
from lab.robot_evidence import checked_rows, complete
from lab.drafts import checkpoint, current
from lab.navigation import bottom_nav
from pages.workflow import field, locked, meaningful, saved_status
from pages.robot_visuals import room_svg
from simulation.robot_room import SCENARIOS, COMMANDS, initial_state, contract, model_message, ROBOT_SYSTEM, MAX_STEPS


def begin(st, case, prompt, comparisons=None):
    try:
        job = start_job("language", case, prompt, "custom" if case == "custom" else "baseline",
                        robot_state=initial_state(), comparison_ids=comparisons)
        st.session_state["control_robot_runs"] = [*st.session_state.get("control_robot_runs", []), job]
        st.session_state["control_robot_active"] = job
        st.rerun()
    except (OSError, ValueError) as error:
        st.error(str(error))


def results(st, row):
    model, receipt = row["record"], row["simulation"]
    st.caption("Request: " + model["prompt"])
    st.image(room_svg(receipt["after"], receipt), width=505)
    st.write("**Model actions:** " + model["output"])
    st.write(f"**Goal visited:** {'Yes' if receipt['goal_reached'] else 'No'} | **Moves:** {receipt['moves']} | **Actions:** {receipt['actions']}")
    st.write(f"**First goal step:** {receipt['first_goal_step'] if receipt['first_goal_step'] is not None else 'Not reached'} | **Blocked moves:** {receipt['blocked_actions']} | **STOP steps:** {receipt['stop_actions']} | **Final position:** {receipt['after']['position']}")
    st.write(receipt["reason"])
    with st.expander("Inspect each action and exactly what the model received", expanded=False):
        st.dataframe([{"Step": n+1, "Position before": str(s["simulation"]["before"]["position"]), "Model action": s["model"]["output"],
                       "Position after": str(s["simulation"]["after"]["position"]), "Result": s["simulation"]["reason"]} for n,s in enumerate(model["steps"])], hide_index=True)
        index = st.selectbox("View model input for step", range(len(model["steps"])), format_func=lambda n: str(n+1), key="step_" + model["job_id"])
        st.code(model["steps"][index]["model"]["model_input"], language="text")


def render(st):
    st.title("Mission 3: Can a better prompt guide a robot through a maze?")
    if locked(st, "mission_2"):
        return
    st.write("A warehouse robot starts at S and must reach the blue target crate at (11,1). Two walls force it to take a detour through the upper and lower openings. The other colored objects are landmarks, not obstacles. Compare three supplied prompts on this same task, then write and test your own improved prompt.")
    st.write("At every step the local language model chooses one action. UP decreases the row, DOWN increases it, LEFT decreases the column, and RIGHT increases it. Each move covers one cell. STOP keeps the robot still for one step. A check blocks moves into walls, then the model receives feedback and chooses again. After a blocked move, its next choice is restricted to free neighboring directions or STOP. This local check does not plan a route or choose a direction for the model.")
    left, right = st.columns([3,2])
    left.image(room_svg(initial_state()), width=505)
    right.markdown("**What does the model know?**")
    right.write("It receives your prompt, the full text map, the robot's current coordinates, the goal, the labeled object locations, which neighboring cells are free, and its most recent actions. It receives updated state before every choice. It does not receive this picture or a computed route.")
    right.code(COMMANDS, language="text")
    right.write("Every run automatically resets the map and position. The same prompt stays in use throughout a run. Every run lasts 50 steps, including blocked moves and STOP actions. Reaching the goal is recorded but does not end the run. At the goal, the model can keep choosing STOP to stay there. An unsuccessful run is valid evidence.")
    with st.expander("See the exact starting input and fixed action instructions"):
        st.code(ROBOT_SYSTEM, language="text", wrap_lines=True)
        st.code(model_message("Your selected prompt appears here.", initial_state()), language="text", wrap_lines=True)
    if not installed():
        st.warning("Prepare the local models on Preflight first. Your work is retained.")
        bottom_nav(st, "mission_2", None)
        return
    active = st.session_state.get("control_robot_active")
    active = active if isinstance(active, str) else None
    status = job_status("language", active) if active else {}
    running = status.get("status") in ("queued", "loading", "generating")
    if running:
        @st.fragment(run_every=1)
        def progress():
            latest = job_status("language", active)
            if latest.get("status") not in ("queued", "loading", "generating"):
                st.rerun()
            st.info(f"Running the robot: action {latest.get('step', 1)} of {MAX_STEPS}. Last action: {latest.get('last_action', 'None yet')}. {latest.get('elapsed', 0):.0f} seconds elapsed.")
            if latest.get("robot_state"):
                st.image(room_svg(latest["robot_state"], {"path":latest["path"]}), width=505)
            if st.button("Cancel this experiment"):
                cancel_job("language", active)
                st.rerun()
        progress()
    elif status.get("status") in ("error", "cancelled"):
        st.warning(status.get("error", "The run stopped. Retry when ready."))
    rows = checked_rows(st.session_state)
    baselines = {case: next((r for r in reversed(rows) if r["record"]["case"] == case and r["record"].get("phase") == "baseline"), None) for case in SCENARIOS}
    st.subheader("1. Run all three supplied prompts")
    st.write("For each prompt, select Run robot with this prompt once. The model chooses and the simulator checks every action automatically. Watch the path, then compare goal visits, blocked moves and pauses across all 50 steps.")
    for case,item in SCENARIOS.items():
        st.markdown("### " + item["label"])
        st.write(item["request"])
        if st.button("Run robot with this prompt", key="robot_run_"+case, disabled=running):
            begin(st, case, item["request"])
        if baselines[case]:
            results(st, baselines[case])
    if all(baselines.values()):
        st.subheader("2. Compare the results, then write your own prompt")
        st.dataframe([{"Prompt": SCENARIOS[r["record"]["case"]]["label"], "Goal visited": r["simulation"]["goal_reached"], "First goal step": r["simulation"]["first_goal_step"], "Blocked moves": r["simulation"]["blocked_actions"], "STOP steps": r["simulation"]["stop_actions"], "Moves": r["simulation"]["moves"], "Final position": str(r["simulation"]["after"]["position"])} for r in baselines.values()], hide_index=True)
        st.write("Compare the green paths with the wall openings. Which prompt helped the robot make progress? Where did it repeat moves, pause, or try to cross a wall? A longer or more detailed prompt does not guarantee a better path. Use those observations to write a fourth prompt in your own words. Give the robot useful route or decision guidance without changing its map or actions.")
        prompt = st.text_area("Your own robot prompt (required)", key="control_robot_custom_prompt", max_chars=1200, height=130)
        valid = bool(prompt.strip()) and prompt.strip() not in [s["request"] for s in SCENARIOS.values()]
        if st.button("Run robot with my prompt", key="robot_run_custom", disabled=running or not valid):
            begin(st, "custom", prompt, [r["record"]["job_id"] for r in baselines.values()])
        own = next((r for r in reversed(rows) if r["record"]["case"] == "custom"), None)
        if own:
            st.markdown("### Your prompt's result")
            results(st, own)
            answer = field(st, "m3_analysis", "Compare your own prompt with one supplied prompt. How did the paths, goal visits, blocked moves or STOP steps differ across the 50 steps? Use one displayed result to explain whether your prompt helped and what limitation remains.")
            ready = complete(rows) and meaningful(answer) and not running and prompt.strip() == own["record"]["prompt"]
            if st.button("Check and save Mission 3", type="primary"):
                if ready:
                    checkpoint("mission_3", st.session_state, {"experiment":"local-robot-v4", "model":MODEL_CONFIG["language"], "simulator_contract":contract()}, rows, {"analysis":answer})
                    st.rerun()
                else:
                    st.warning("Run your current prompt after all three examples, then write at least 15 words about a specific result. The robot does not have to succeed.")
    else:
        st.info("Run all three supplied prompts to unlock your own prompt experiment.")
    saved_status(st, "mission_3")
    bottom_nav(st, "mission_2", "final_submission", next_disabled=not current("mission_3", st.session_state))
