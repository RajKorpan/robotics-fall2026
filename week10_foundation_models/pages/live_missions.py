"""Compare three live outputs before writing a required personal prompt."""
from lab.local_config import LANGUAGE_TASKS, VISION_TASKS, VISION_REFERENCE, CAPABILITIES, MODEL_CONFIG, scene_path
from lab.local_jobs import start_job, job_status, cancel_job, installed, live_records, records_complete, compatible_record
from lab.drafts import checkpoint, current
from lab.navigation import bottom_nav
from pages.workflow import field, locked, meaningful, saved_status
from pages.guided_visuals import mission_one_setup


def job_panel(st, kind, job_id):
    @st.fragment(run_every=1)
    def poll():
        status = job_status(kind, job_id)
        if status["status"] in ("complete", "error", "cancelled"):
            if st.session_state.get("seen_job_" + job_id) != status["status"]:
                st.session_state["seen_job_" + job_id] = status["status"]
                st.rerun()
            return
        st.info({"queued": "Waiting for the local model", "loading": "Loading model weights into memory", "generating": "Generating a new answer on your computer"}.get(status["status"], status["status"]) + f". Elapsed: {status.get('elapsed', 0):.0f} s. Generated tokens: {status.get('tokens', 0)}.")
        if st.button("Stop this run", key="stop_" + job_id):
            cancel_job(kind, job_id)
            st.rerun()
    poll()


def begin(st, kind, case, prompt, comparisons=None):
    try:
        job = start_job(kind, case, prompt, "custom" if case == "custom" else "baseline", comparison_ids=comparisons)
        key = "control_live_" + kind + "_runs"
        st.session_state[key] = [*st.session_state.get(key, []), job]
        st.session_state["control_live_" + kind + "_active"] = job
        st.rerun()
    except (OSError, ValueError) as error:
        st.error(str(error))


def render_mission(st, kind):
    language = kind == "language"
    mission = "mission_1" if language else "mission_2"
    number = 1 if language else 2
    tasks = LANGUAGE_TASKS if language else VISION_TASKS
    st.title("Mission 1: Can the model understand the robot's task?" if language else "Mission 2: How does your question change what the model tells you?")
    if not language and locked(st, "mission_1"):
        return
    st.write("Run all three example requests and read their actual answers. Compare what each answer gets right, assumes, or overlooks. Then write one improved request of your own and test it with the same robot capability card." if language else "A robot is helping at a workbench. Use the same photograph for three different questions: identifying a tool, describing its location, and choosing an object for a task. Compare the answers before writing a clearer question of your own.")
    st.caption("Local model: " + MODEL_CONFIG[kind]["id"] + ". Each run generates a new answer on your computer.")
    if language:
        st.image(mission_one_setup(), width=610)
        st.caption("Starting setup, shown schematically. The model receives the capability card below as text, not this diagram or a live camera view.")
        with st.container(border=True):
            st.markdown("**Robot capability card supplied with every request**")
            st.write(CAPABILITIES)
            st.caption("The model proposes a plan. No robot moves and no new camera image is taken in this mission.")
    else:
        st.image(str(scene_path()), width=640)
        st.caption("Workbench and tools, Jeff Sheldon, CC0. All questions use these exact same image pixels.")
    if not installed():
        st.warning("Prepare the local models on Preflight first. Your work is retained.")
        bottom_nav(st, "guided" if language else "mission_1", None)
        return
    active = st.session_state.get("control_live_" + kind + "_active")
    status = job_status(kind, active) if active else {}
    running = status.get("status") in ("queued", "loading", "generating")
    rows = [r for r in live_records(mission, st.session_state) if compatible_record(kind, r)]
    originals = {case: next((r for r in reversed(rows) if r["case"] == case and r["phase"] == "baseline" and r["prompt"] == task["prompt"]), None) for case, task in tasks.items()}
    st.subheader("1. Generate all three answers and compare")
    for column, (case, task) in zip(st.columns(3), tasks.items()):
        column.markdown("**" + task["label"] + "**")
        column.write(task["prompt"])
        if column.button("Run this request" if not originals[case] else "Run again", key="run_" + kind + "_" + case, disabled=running, width="stretch"):
            begin(st, kind, case, task["prompt"])
        if originals[case]:
            column.info(originals[case]["output"])
            column.caption(f"Generated in {originals[case]['generation_seconds']:.1f} s")
        else:
            column.caption("The model's answer will appear here.")
    if running:
        job_panel(st, kind, active)
    elif status.get("status") in ("error", "cancelled"):
        st.warning(status.get("error", "This run stopped. Try again."))
    all_three = all(originals.values())
    if not all_three:
        st.info("Generate the answer for each of the three requests. The next part appears once all three answers are available.")
        saved_status(st, mission)
        bottom_nav(st, "guided" if language else "mission_1", "mission_2" if language else "mission_3", next_disabled=True)
        return
    st.write("**Compare before revising:** Which answer uses only the available information? Which one guesses, ignores a limitation, or needs clarification? Keep these three answers visible while designing your own request." if language else "**Compare before revising:** Do the answers identify the same objects? Is the spatial claim visible in the photograph? Does the third question supply enough information to choose a correct tool? A confident answer is not proof that the robot's task is known.")
    if not language:
        with st.expander("Check the visible evidence"):
            st.write(VISION_REFERENCE)
            st.caption("This authored reference is not sent to the model.")
    st.subheader("2. Write an improved request of your own")
    if language:
        st.write("Use what you noticed in all three examples. Write a clear, feasible request that names the intended object and destination, or explicitly asks for missing information. You may combine useful parts of the examples. This is your required fourth experiment.")
    else:
        st.write("Choose ONE task below for your fourth experiment. State the chosen task and its goal at the start of your new request. You are improving the model's answer for that task, rather than asking it to identify, locate and decide all at once.")
        st.table([
            {"Choose a task": "Identify", "Robot's goal": "Identify the tool in the foreground. Ask for visible features supporting the name and for uncertainty if the identity is unclear."},
            {"Choose a task": "Locate", "Robot's goal": "Locate the black vertical post relative to the foreground tool. Ask for an image-based spatial description, without inventing physical distances or world coordinates."},
            {"Choose a task": "Decide", "Robot's goal": "The robot is preparing to mark a circle on a flat wooden workpiece. Ask which visible tool could help, what image evidence supports the choice, and what must be checked before the robot could use it."},
        ])
        st.write("Keep the same photograph. Write the request in your own words, make the selected goal explicit, and ask the model to separate visible evidence from assumptions. For Decide, supplying the missing job is part of the improvement: the original request never said what the robot needed the tool for.")
        st.caption("After generating the new answer, compare it with the original answer for your selected task. Use the other two examples to notice problems, but do not treat answers to different tasks as a direct comparison of quality.")
    key = "control_live_" + kind + "_custom_prompt"
    own = st.text_area("Your improved request", key=key, max_chars=1200, height=115)
    changed = bool(own.strip()) and own.strip() not in [t["prompt"] for t in tasks.values()]
    if st.button("Run my improved request", key="run_" + kind + "_custom", disabled=running or not changed, type="primary"):
        begin(st, kind, "custom", own, [r["job_id"] for r in originals.values()])
    customs = [r for r in rows if r["case"] == "custom" and r["phase"] == "custom"]
    custom = customs[-1] if customs else None
    if custom:
        st.markdown("**Answer to your improved request**")
        st.caption("Generated for: " + custom["prompt"])
        st.info(custom["output"])
        st.caption(f"Generated in {custom['generation_seconds']:.1f} s. Compare it with all three original answers above.")
        if own.strip() != custom["prompt"]:
            st.caption("The text box has changed since this answer was generated. Run it again to evaluate your new wording.")
    if not custom:
        st.caption("Generate an answer to your own request to reveal the final question.")
        bottom_nav(st, "guided" if language else "mission_1", "mission_2" if language else "mission_3", next_disabled=True)
        return
    st.subheader("3. Explain and save")
    answer = field(st, "m1_analysis" if language else "m2_analysis", "Did your revised request improve the response? Point to one specific difference and explain whether the proposed actions fit the robot's capabilities." if language else "Which task did you choose, and did your revised request produce a better answer for that goal than the original request for the same task? Point to one specific difference and use visible evidence from the photograph to explain your judgment.")
    ready = records_complete(mission, rows) and meaningful(answer) and not running and own.strip() == custom["prompt"]
    if st.button("Check and save Mission " + str(number), type="primary"):
        if ready:
            checkpoint(mission, st.session_state, {"experiment": "local-live-v2", "model": MODEL_CONFIG[kind]}, rows, {"analysis": answer})
            st.rerun()
        else:
            st.warning("Finish the three examples, run your current improved request, and write at least 15 words using a specific result. Incorrect model answers can be saved.")
    saved_status(st, mission)
    bottom_nav(st, "guided" if language else "mission_1", "mission_2" if language else "mission_3", next_disabled=not current(mission, st.session_state))
