"""Lab 10 guide for the individual voice and shared-control handover."""
import argparse
from copy import deepcopy
from tempfile import TemporaryFile
from handover import CHECK_GROUPS, FEEDBACK, MODES, interpret, load_controller, scripted_checks
from lab.storage import (LAB_DIR, archive, bundle, draft_backup, export, export_current, load,
                         planner_source, resume_trial, root, save, submission_files)

TITLE = "Lab 10 · Voice, Shared Control, and Assistive Handover"
STAGES = ("Introduction", "Microphone check", "Hear, interpret, clarify", "Trace the handover",
          "Fix one rule and replay it", "See who is in control", "Mission 1", "Mission 2",
          "Mission 3", "Synthesis and submission")
SYNTHESIS = ("Which mode would you choose for a routine handover, and which when the person's needs may change mid-task? "
             "Cite results from the three modes and explain how your voice redesign affected one observed interaction.")
MODE_SCENARIOS = {"normal": "Normal handover", "changed": "Changed goal"}


def complete_voice(work):
    from experiments import VOICE_CASES
    redesign, retest = work.get("redesign"), work.get("retest")
    return (set(VOICE_CASES) <= set(work.get("voice", {}))
            and all(work["voice"][key].get("ros", {}).get("backend") == "ROS 2 / Gazebo" for key in VOICE_CASES)
            and bool(redesign and retest and retest["redesign"] == redesign
                     and retest["state"]["scenario"] == redesign["case"]
                     and work.get("voice_analysis", "").strip()))


def complete_modes(work):
    return all(work.get("modes", {}).get(f"{index}-{scenario}", {}).get("ros", {}).get("backend") == "ROS 2 / Gazebo"
               for index in range(len(MODES)) for scenario in MODE_SCENARIOS)


def mission_one_current(work):
    checked = work.get("mission_1", {})
    path = root() / "mission_1" / "controller.py"
    return (bool(checked.get("checks"))
            and all(row["passed"] and "first_mismatch" in row for row in checked["checks"])
            and bool(checked.get("explanation", "").strip())
            and checked["explanation"] == work.get("guard_explanation")
            and path.is_file() and path.read_text(encoding="utf-8-sig") == checked["source"]
            and work.get("practice", {}).get("ros", {}).get("backend") == "ROS 2 / Gazebo"
            and work.get("practice_source") == checked["source"])


def furthest(work):
    if not work.get("mic"):
        return 1
    reviewed = work.get("tutorial_reviewed", 0)
    if reviewed < 4:
        return reviewed + 2
    if not mission_one_current(work):
        return 6
    if not complete_voice(work):
        return 7
    return 9 if complete_modes(work) else 8


def preflight(st, work):
    from experiments import decoder
    from speech import transcribe

    st.title("ROS, microphone, and saving check")
    st.write("The guide runs in the course ROS container. Open the virtual desktop beside the guide. Your computer's browser records your microphone and sends the clip to the guide for local transcription.")
    st.markdown("**Terminal 1 in the virtual desktop**")
    st.write("Start the cup delivery room. This launches Gazebo, bridges odometry and velocity messages, and starts the ROS interaction controller. Leave it running throughout the lab.")
    st.code("cd /workspace/week11_hri_evaluation\nbash scripts/launch_handover.sh", language="bash")
    st.markdown("**In this guide**")
    from ros_client import available
    status = available()
    if st.button("Refresh ROS checks"):
        st.rerun()
    if status.get("ready"):
        st.success("ROS controller connected. Gazebo is publishing fresh /odom.")
        from ros_client import client
        if client().image:
            st.image(client().image, caption="The Gazebo room. Green is the person station, yellow the correction checkpoint, and red and blue the cup stations.", width="stretch")
    else:
        st.info("Waiting for the Gazebo world and ROS controller. Run the command in Terminal 1, wait for the robot to appear, and refresh the checks.")
        with st.expander("ROS checks still waiting or an old topic command hangs?"):
            st.write("The current controller is lab10_interaction and the guide sends requests on /lab10/input. An old week11_interaction_demo node or /hri/command instruction belongs to the previous lab. Stop that demo with Ctrl+C, restart the current guide using the course launcher, and launch the handover world above.")
            st.write("In a second virtual-desktop terminal, run these checks. Sourcing ros_env.sh selects this lab's workspace and ROS domain 31 in that terminal.")
            st.code("cd /workspace/week11_hri_evaluation\nsource scripts/ros_env.sh\nros2 node list\nros2 topic info /lab10/input --verbose",language="bash")
            st.write("Expect /lab10_interaction and a subscription on /lab10/input. If either is absent, inspect Terminal 1 for launch errors and copy the output for the instructor. You do not need ros2 topic pub commands to complete preflight.")
    st.write("Use the microphone button below to record “Bring me the blue cup.” Stop recording, play the clip back, and select Check recording.")
    st.caption("If the recorder never starts, allow microphone access in your browser's site settings and check that your operating system allows the browser to use the microphone. If playback is quiet, select the correct microphone in your sound settings and try again.")
    st.caption("The recorder sends this clip to the local guide for transcription. Saved lab evidence contains text and controller events.")
    audio = st.audio_input("Test microphone", sample_rate=16000, key="lab10-mic")
    writable = False
    try:
        root().mkdir(parents=True, exist_ok=True)
        with TemporaryFile(dir=root()) as probe:
            probe.write(b"Lab 10")
        writable = True
    except OSError as error:
        st.error(f"The guide could not write to {root()}. Check folder permissions. {error}")
    if st.button("Check recording", disabled=audio is None):
        st.session_state.lab10_mic = False
        try:
            phrase = transcribe(decoder(), audio.getvalue())
            if not phrase:
                st.warning("No command was recognized. Try speaking one short phrase close to the microphone.")
            transcript = phrase or "(no match)"
            work["mic"] = transcript
            st.session_state.lab10_mic = True
        except ImportError:
            st.error("The speech package is missing. Install the lab requirements in the environment running the guide, then restart it.")
        except ValueError as error:
            st.error(f"The clip could not be used. Check playback and try recording again. {error}")
        except (RuntimeError, OSError) as error:
            st.error(f"The local speech recognizer could not run. {error}")
    checked = st.session_state.get("lab10_mic", False)
    if checked:
        st.success(f"Local transcript · {work['mic']}")
        st.write("Compare the transcript with your words. A mismatch is worth noticing. The controller receives the transcript during voice trials.")
    st.table([{"Check": "Microphone and recognizer", "Result": work.get("mic") if checked else "Record and check a new clip"},
              {"Check": "Saving folder", "Result": "Writable" if writable else "Check permissions"}])
    return checked and writable and status.get("ready", False)


def mission_one(st, work):
    st.title("Mission 1 · Build and verify the interaction")
    st.write("Complete the controller here, test its rules, then run it on the Gazebo robot. Your function receives a phase and event and returns a decision. The ROS node uses that decision to authorize movement, stop, or finish the handover.")
    from visuals import controller_editor
    path = controller_editor(work, "mission1")
    st.code('CONFIRM state + CONFIRM event → decide returns "begin" → ROS node authorizes movement',
            language=None)
    rules = [
        {"When": "REQUEST arrives in IDLE, CLARIFY, CONFIRM, RECOVERY, or CANCELLED",
         "Return": "select for a named cup, clarify if the target is missing"},
        {"When": "CORRECT names a cup during an active task",
         "Return": "select, which stops the old task and clears its confirmation"},
        {"When": "CONFIRM arrives in CONFIRM", "Return": "begin"},
        {"When": "TICK arrives in EXECUTING", "Return": "advance"},
        {"When": "READY arrives in WAIT_READY", "Return": "release"},
        {"When": "CANCEL arrives during an active interaction", "Return": "cancel before other rules"},
        {"When": "TIMEOUT arrives while waiting for readiness", "Return": "timeout"},
        {"When": "An event has no valid transition", "Return": "hold"},
    ]
    st.write("Inspect `event['kind']` and `event['target']` along with `state['phase']`. A named target is `red` or `blue`. Save in your editor before checking each group.")
    source = path.read_text(encoding="utf-8-sig")
    groups = {
        "Select and confirm": (rules[:3], "Resolve which cup the person wants. A correction must clear the earlier confirmation."),
        "Offer and release": (rules[3:5], "Advance toward the station. Release only when offering the cup and receiving READY."),
        "Interrupt and recover": (rules[5:], "Give cancellation priority. Handle an expired offer and hold for inputs without a valid transition."),
    }
    group = None
    run_checks = False
    for name in CHECK_GROUPS:
        group_rules, instruction = groups[name]
        with st.expander(name):
            st.write(instruction)
            st.table(group_rules)
            if st.button(f"Check {name.lower()}"):
                group = name
                run_checks = True
    if st.button("Run all scripted checks", key="m1-run"):
        run_checks = True
    if run_checks:
        try:
            checks = scripted_checks(load_controller(source, str(path)), group)
            work["current_checks"] = {"source": source, "checks": checks, "group": group}
        except Exception as error:
            work.pop("current_checks", None)
            st.error(f"Could not run the controller. {error}")
    checked = work.get("current_checks", {})
    checks = checked.get("checks", [])
    if checks:
        st.caption(f"Showing {checked.get('group') or 'all scripted checks'}.")
        st.table([{"Case": row["case"], "Result": "Pass" if row["passed"] else "Needs work",
                   "Final state": row["final_state"]["phase"]} for row in checks])
        selected = st.selectbox("Inspect a scripted trace", range(len(checks)),
                                format_func=lambda index: checks[index]["case"],
                                key=f"m1-trace-{checked.get('group')}")
        mismatch = checks[selected].get("first_mismatch")
        if mismatch:
            st.write(f"First unexpected transition at step {mismatch['step']}. Inspect the event and phase before changing your rule.")
            st.json(mismatch, expanded=True)
        st.dataframe([{"Event": row["event"], "Decision": row["decision"],
                       "Before": row["before"]["phase"], "After": row["after"]["phase"],
                       "Delivered": row["after"]["delivered"]} for row in checks[selected]["trace"]])
    explanation = st.text_area("Explain one guard and point to an event in its trace.",
                               value=work.get("guard_explanation", ""), key="m1-explain")
    work["guard_explanation"] = explanation
    checks_ready = (checks and "group" in checked and checked["group"] is None
                    and checked.get("source") == source and all(row["passed"] for row in checks))
    if not checks_ready or not explanation.strip():
        st.info("To save, pass the full check suite on your current file and explain one guard using a trace event.")
    st.subheader("Test your controller on the Gazebo robot")
    st.write("After passing all scripted checks, reset the world in Terminal 2. Start the trial below, request blue, confirm it, and watch the robot drive to the blue pad and return. Select Ready when it offers the cup at the green pad.")
    st.code("cd /workspace/week11_hri_evaluation\nbash scripts/reset_handover.sh", language="bash")
    st.caption("The robot represents cup loading and transfer using a simulated tray state. Its navigation and arrival are measured through Gazebo and ROS odometry.")
    from experiments import start, trial_panel
    from ros_client import available
    if st.button("Start ROS controller trial", disabled=not checks_ready or bool(work.get("active")) or not available().get("ready")):
        start(work, "practice", "practice", MODES[1], "normal")
        st.rerun()
    if work.get("active", {}).get("group") == "practice":
        trial_panel(work)
    practice_ready = (work.get("practice_source") == source
                      and work.get("practice", {}).get("ros", {}).get("distance_m", 0) > .5)
    if not practice_ready:
        st.info("Finish and save the ROS trial, including an unsuccessful attempt with an explanation, before saving Mission 1.")
    if st.button("Check and save Mission 1", disabled=not (checks_ready and explanation.strip() and practice_ready)):
        previous = work.get("mission_1", {}).get("source")
        if previous is not None and previous != source:
            archive(work, "Evidence from previous controller",
                    {key: work.pop(key) for key in ("mission_1", "voice", "redesign", "retest",
                                                   "voice_analysis", "modes") if key in work})
            st.session_state.pop("m2-analysis", None)
        work["mission_1"] = {"source": source, "checks": checks, "explanation": explanation}
        save(work)
        st.success("Mission 1 saved.")
    if not mission_one_current(work):
        st.caption("Next becomes available after saving your current checks and explanation.")
    return mission_one_current(work)


def mission_two(st, work):
    from experiments import VOICE_CASES, row_view, saved_traces, start, summary, trial_panel

    st.title("Mission 2 · Voice trials, redesign, and retest")
    st.write("Run each case with your microphone. Enter what you intend to say, record it, and compare your words with the transcript. If the robot asks which cup, repair the request by naming a color. Watch the robot respond in Gazebo and inspect its ROS event trace here.")
    st.write("Before a new trial, finish or archive the old one, then reset the world in Terminal 2 and wait for the robot to return to the green pad.")
    st.code("cd /workspace/week11_hri_evaluation\nbash scripts/reset_handover.sh", language="bash")
    st.caption("Spoken Confirm and Ready require you to approve what the guide heard. If it heard permission you did not give, select Keep waiting.")
    voice = work.get("voice", {})
    active = work.get("active")
    case = st.selectbox("Voice scenario", list(VOICE_CASES), format_func=lambda key: VOICE_CASES[key][0])
    st.write(VOICE_CASES[case][1])
    if st.button("Start voice trial", disabled=active is not None):
        start(work, "voice", case, MODES[1], case)
        st.rerun()
    if active and active["group"] in ("voice", "retest"):
        trial_panel(work)
    st.table([{"Required case": label, "Outcome": voice[key]["outcome"] if key in voice else "Still to run"}
              for key, (label, _, _) in VOICE_CASES.items()])
    saved_traces({VOICE_CASES[key][0]: record for key, record in voice.items()})

    if set(VOICE_CASES) <= set(voice):
        st.subheader("Redesign one piece of feedback")
        st.write("Open a baseline trace and find a moment where the person needed clearer information. Note its state, write replacement feedback for that state, and repeat the same scenario.")
        prior = work.get("redesign", {})
        with st.form("redesign"):
            case_keys = list(VOICE_CASES)
            scenario = st.selectbox("Repeat this voice scenario", case_keys,
                                    index=case_keys.index(prior.get("case", "clear")),
                                    format_func=lambda key: VOICE_CASES[key][0])
            phases = list(FEEDBACK)
            phase = st.selectbox("State whose feedback you will change", phases,
                                 index=phases.index(prior.get("phase", "CONFIRM")))
            message = st.text_input("Revised feedback", value=prior.get("message", ""), max_chars=240)
            rationale = st.text_area("Which baseline event prompted this change, and what should the person understand?",
                                     value=prior.get("rationale", ""))
            st.caption("Use {target} where the displayed message should include the selected cup color.")
            if st.form_submit_button("Save redesign", disabled=active is not None):
                observed_phases = {row["after"]["phase"] for row in voice[scenario]["events"]}
                if phase not in observed_phases:
                    st.warning("Choose a state that appears in the selected baseline trace.")
                elif message.strip() and rationale.strip() and message.strip() != FEEDBACK[phase]:
                    redesign = {"case": scenario, "phase": phase, "message": message.strip(),
                                "rationale": rationale.strip()}
                    if work.get("redesign") != redesign:
                        archive(work, "Evidence before feedback redesign changed",
                                {key: work.pop(key) for key in ("redesign", "retest", "voice_analysis", "modes")
                                 if key in work})
                        st.session_state.pop("m2-analysis", None)
                    work["redesign"] = redesign
                else:
                    st.warning("Enter a changed message and link it to a baseline observation.")
        redesign = work.get("redesign")
        if redesign:
            st.write(f"Saved redesign for {VOICE_CASES[redesign['case']][0]} during {redesign['phase']}.")
            if st.button("Start matched voice retest", disabled=active is not None):
                start(work, "retest", redesign["case"], MODES[1], redesign["case"], deepcopy(redesign))
                st.rerun()
        retest = work.get("retest")
        if redesign and retest and retest["redesign"] == redesign:
            baseline = voice[redesign["case"]]
            phase = redesign["phase"]
            st.subheader("Compare the same moment")
            st.write(f"Find where each run first reached {phase}. Compare what the recognizer heard, what the controller did, and what the person saw.")
            cols = st.columns(2)
            for col, label, record in zip(cols, ("Baseline", "Retest"), (baseline, retest)):
                with col:
                    st.markdown(f"**{label}**")
                    matched = next((row for row in record["events"] if row["after"]["phase"] == phase), None)
                    if matched:
                        st.table([row_view(matched)])
                    else:
                        st.write("This run did not reach the selected state.")
                    st.write(f"Outcome · {record['outcome']}")
            saved_traces({"Matched voice retest": retest})
            work["voice_analysis"] = st.text_area(
                "Compare one baseline and retest event. What changed in the transcript, feedback, or outcome?",
                value=work.get("voice_analysis", ""), key="m2-analysis")
    if not complete_voice(work):
        st.caption("Next requires all four cases, a saved redesign, its matched retest, and your comparison.")
    return complete_voice(work) and active is None


def mission_three(st, work):
    from experiments import saved_traces, start, summary, trial_panel

    st.title("Mission 3 · Compare three control modes")
    st.write("Run a normal handover and a changed goal in each mode. Every run starts in the same layout with blue as the initial goal. For the changed-goal run, switch to red at the marked checkpoint before either cup is picked up.")
    st.markdown(
        "- **Manual teleoperation.** Drive using W/S/A/D in Terminal 3. Dock at the selected pad, select Load cup at station, drive back to the green pad, and select Offer at person. Use Change goal to red at the yellow checkpoint.\n"
        "- **Shared autonomy with voice.** Speak the blue-cup request and confirm it. At the checkpoint, speak the red-cup correction and confirm the new goal.\n"
        "- **Autonomous execution.** Set blue and select Run supplied autonomy. At the checkpoint, select Stop, set red, and run it again."
    )
    st.write("All modes use the same Gazebo room, Ready control, and Stop control. The supplied autonomous policy drives to the station and returns. Select Ready only when the robot has returned and offers the cup.")
    st.markdown("**Before each trial**")
    st.write("Finish or archive the previous attempt. In Terminal 2 run the reset command and wait for the robot to return to the green pad. Start the selected mode trial below. This begins its timer.")
    st.code("cd /workspace/week11_hri_evaluation\nbash scripts/reset_handover.sh", language="bash")
    mode = st.selectbox("Control mode", MODES)
    scenario = st.selectbox("Scenario", list(MODE_SCENARIOS), format_func=MODE_SCENARIOS.get)
    active = work.get("active")
    key = f"{MODES.index(mode)}-{scenario}"
    if st.button("Start mode trial", disabled=active is not None):
        start(work, "modes", key, mode, scenario, work["redesign"])
        st.rerun()
    if active and active["group"] == "modes":
        trial_panel(work)

    records = work.get("modes", {})
    st.subheader("Six-trial comparison")
    rows, labeled = [], {}
    for index, mode_label in enumerate(MODES):
        for scenario_key, scenario_label in MODE_SCENARIOS.items():
            label = f"{mode_label} / {scenario_label}"
            record = records.get(f"{index}-{scenario_key}")
            rows.append(summary(label, record) if record else {"Trial": label, "Outcome": "Still to run"})
            if record:
                labeled[label] = record
    st.dataframe(rows, hide_index=True)
    saved_traces(labeled)
    st.caption("Time includes recording, review, and operator decisions from Start mode trial to transfer or early end. Paused guide time is excluded. Inputs include voice commands, permission reviews, and keyboard commands. Compare the actual intervention and delivered cup using the ROS event traces.")
    if not complete_modes(work):
        st.caption("Save one normal run and one changed-goal run in each of the three modes to continue.")
    return complete_modes(work) and active is None


def final_page(st, work):
    from lab.final_reflection import render_final_reflection, RESPONSE_KEY

    st.title("Synthesis and submission")
    synthesis = st.text_area(SYNTHESIS, value=work.get("synthesis", ""), key="lab10-synthesis")
    work["synthesis"] = synthesis
    st.session_state.setdefault("responses", {RESPONSE_KEY: work.get("reflection", "")})
    reflection_ready = render_final_reflection(st)
    reflection = st.session_state["responses"][RESPONSE_KEY]
    work["reflection"] = reflection
    checks = [
        ("Mission 1 checks and guard explanation match the current controller", mission_one_current(work)),
        ("Four voice trials, feedback redesign, matched retest, and comparison", complete_voice(work)),
        ("Six mode trials", complete_modes(work)),
        ("Technical synthesis", bool(synthesis.strip())),
        ("Course reflection", reflection_ready),
    ]
    st.table([{"Requirement": label, "Status": "Ready" if passed else "Still to complete"} for label, passed in checks])
    can_export = all(passed for _, passed in checks)
    files = submission_files(work, synthesis, reflection) if can_export else {}
    if st.button("Save complete submission", type="primary", disabled=not can_export):
        try:
            export(files)
        except (OSError, ValueError) as error:
            st.error(f"Submission could not be saved. {error}")
        else:
            st.success(f"Saved to {root()}")
    if can_export and export_current(files):
        st.download_button("Download submission ZIP", bundle(files, "student_submission"),
                           file_name="lab10_submission.zip", mime="application/zip", on_click="ignore")
    elif (root() / "manifest.json").exists():
        st.info("Your saved submission differs from the current work. Save again before submitting.")
    st.write("Inspect the submission folder, commit and push it to your course fork, and submit the commit link.")


def run_app():
    import streamlit as st
    from tutorial import render as tutorial

    st.set_page_config(page_title=TITLE, layout="wide")
    if "lab10_work" not in st.session_state:
        try:
            work = load()
            if work.get("schema") != 3:
                previous = {key: work.pop(key) for key in ("voice", "retest", "redesign",
                                                           "voice_analysis", "modes", "active", "practice") if key in work}
                if previous:
                    archive(work, "Previous lab revision evidence", previous)
                    work["updated_trial_rules"] = True
                work["tutorial_reviewed"] = 0
                work["schema"] = 3
            st.session_state.lab10_work = work
            if work.get("stage", 0) > 1:
                st.session_state.lab10_resume = work["stage"]
        except (OSError, ValueError) as error:
            st.error(f"Progress could not be read. Keep the existing progress file and check its location. {error}")
            return
    work = st.session_state.lab10_work
    resume = st.session_state.get("lab10_resume")
    unlocked = furthest(work)
    stage = 1 if resume is not None else min(work.get("stage", 0), unlocked)
    if resume is None:
        work["stage"] = stage
    active = work.get("active")
    if active and unlocked < (8 if active["group"] == "modes" else 6 if active["group"] == "practice" else 7):
        archive(work, "Interrupted trial before prerequisites changed", work.pop("active"))
        active = None
        st.info("The guide archived your active trial because its prerequisites changed. You can recover its trace from the draft backup.")

    def go(next_stage):
        work["stage"] = next_stage
        save(work)
        st.session_state.lab10_scroll_top = True
        st.rerun()

    if st.session_state.pop("lab10_scroll_top", False):
        import streamlit.components.v1 as components
        components.html("""<script>const p=window.parent;const m=p.document.querySelector('[data-testid="stMain"]');if(m)m.scrollTo(0,0);p.scrollTo(0,0);</script>""", height=0)
    st.sidebar.progress((stage + 1) / len(STAGES), text=f"{stage + 1} of {len(STAGES)}")
    for index, label in enumerate(STAGES):
        if st.sidebar.button(label, key=f"lab10-nav-{index}",
                             disabled=index > unlocked or index == stage or active is not None or resume is not None):
            go(index)
    backup_slot = st.sidebar.empty()
    st.sidebar.caption("The draft contains local progress and your controller, including unfinished work.")
    if work.get("recovered_backup"):
        st.warning("The guide recovered the last readable backup. Review your most recent work before continuing.")
    if work.get("updated_trial_rules"):
        st.info("Earlier work is in your draft backup. This revision uses Gazebo and ROS 2. Complete the guided activities and collect fresh robot trials.")
    if st.session_state.get("lab10_ros_error"):
        st.error(st.session_state.pop("lab10_ros_error"))
    if active and resume is None:
        st.caption("Finish or archive the active trial to switch pages.")
        if st.sidebar.button("Stop robot", type="primary", key="lab10-always-stop"):
            from handover import event
            from ros_client import send
            try:
                send(active, event("STOP"))
                save(work)
                st.rerun()
            except RuntimeError as error:
                st.error(str(error))

    ready = True
    if stage == 0:
        st.title(TITLE)
        st.write("Build an interaction controller for a TurtleBot3 in Gazebo, test it with your own voice through ROS 2, and compare manual, shared, and autonomous control. Work individually.")
        st.write("You will check when the robot should ask for clarification, what it should tell the person, and when it should wait for permission. Each mission produces evidence you will use in the final synthesis.")
    elif stage == 1:
        ready = preflight(st, work)
    elif stage <= 5:
        ready = tutorial(stage - 2, work)
    elif stage == 6:
        ready = mission_one(st, work)
    elif stage == 7:
        ready = mission_two(st, work)
    elif stage == 8:
        ready = mission_three(st, work)
    else:
        final_page(st, work)

    st.divider()
    back, forward = st.columns(2)
    if resume is not None:
        target = min(resume, unlocked)
        if forward.button(f"Resume · {STAGES[target]}", disabled=not ready, type="primary", width="stretch"):
            if active:
                resume_trial(active)
            st.session_state.pop("lab10_resume")
            go(target)
    elif stage and back.button(f"Back to {STAGES[stage - 1]}", disabled=active is not None, width="stretch"):
        go(stage - 1)
    if resume is None and stage < len(STAGES) - 1 and forward.button(
            f"Next · {STAGES[stage + 1]}", disabled=not ready or active is not None,
            type="primary", width="stretch"):
        if 2 <= stage <= 5:
            work["tutorial_reviewed"] = max(work.get("tutorial_reviewed", 0), stage - 1)
        go(stage + 1)
    try:
        if not (resume is not None and active):
            save(work)
        backup_slot.download_button("Download draft backup", draft_backup(work), file_name="lab10_draft.zip",
                                    mime="application/zip", on_click="rerun")
        st.sidebar.caption("Saved progress is stored locally.")
    except OSError as error:
        st.error(f"Could not save progress. Keep the guide open and check folder permissions. {error}")


def main():
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--smoke-test", action="store_true")
    if parser.parse_args().smoke_test:
        from speech import make_decoder
        make_decoder()
        assert interpret("bring me the cup") == {"kind": "REQUEST", "target": None}
        starter = (LAB_DIR / "controller_starter.py").read_text(encoding="utf-8")
        assert not all(row["passed"] for row in scripted_checks(load_controller(starter)))
        print("Lab 10 smoke test passed.")
    else:
        run_app()


if __name__ == "__main__":
    main()
