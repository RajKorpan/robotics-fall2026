from __future__ import annotations

from lab.models import RunResult
from lab.navigation import set_stage
from lab.session import mark_checked, mark_complete, set_response, store_run
from lab.submissions import save_mission
from lab_config import LAB
from missions import MISSIONS
from simulation.plotting import feedback_figure


def _render_requirements(st, check) -> None:
    rows = [
        {
            "Requirement": item.label,
            "Actual": item.actual,
            "Expected": item.expected,
            "Passed": "Yes" if item.passed else "No",
        }
        for item in check.requirements
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


def render(st) -> None:
    mission_id = str(st.session_state.get("active_mission", LAB.missions[0]))
    completed = list(st.session_state.get("completed_missions", []))
    if mission_id not in MISSIONS:
        mission_id = LAB.missions[0]
    mission = MISSIONS[mission_id]

    st.title(mission.title)
    st.write(mission.objective)
    st.caption(f"Completed: {len(completed)}/{len(LAB.missions)} missions")

    settings = mission.render_controls(st)
    settings_signature = repr(sorted(settings.items()))
    signature_key = f"{mission_id}_settings_signature"
    previous_signature = st.session_state.get(signature_key)
    if previous_signature is not None and previous_signature != settings_signature:
        runs = dict(st.session_state.get("latest_runs", {}))
        runs.pop(mission_id, None)
        st.session_state["latest_runs"] = runs
        checked = dict(st.session_state.get("checked_run_ids", {}))
        checked.pop(mission_id, None)
        st.session_state["checked_run_ids"] = checked
    st.session_state[signature_key] = settings_signature

    if st.button("Run experiment", type="primary", key=f"run_{mission_id}"):
        with st.spinner("Running experiment..."):
            store_run(st, mission.run(settings))

    result: RunResult | None = st.session_state.get("latest_runs", {}).get(mission_id)
    if result is None:
        st.info("Adjust the controls, then run the experiment.")
        return

    st.pyplot(feedback_figure(result.traces))
    st.subheader("Measured results")
    st.json(result.metrics)
    check = mission.evaluate(result)
    _render_requirements(st, check)

    explanations: dict[str, str] = {}
    for prompt in mission.reflection_prompts:
        key = f"{mission_id}.{prompt.id}"
        answer = st.text_area(
            prompt.label,
            value=st.session_state.get("responses", {}).get(key, ""),
            help=prompt.help or None,
            key=f"reflection_{key}",
        )
        set_response(st, key, answer)
        explanations[prompt.id] = answer

    reflections_ready = all(answer.strip() for answer in explanations.values())
    if check.passed:
        st.success(check.summary)
    else:
        st.warning("The run does not yet meet every mission requirement.")

    checked_run = st.session_state.get("checked_run_ids", {}).get(mission_id)
    if check.passed and reflections_ready and checked_run != result.run_id:
        if st.button("Check and save mission", type="primary", key=f"check_{mission_id}"):
            mark_checked(st, result)
            save_mission(result, check, explanations)
            st.rerun()
    elif not reflections_ready:
        st.info("Complete every explanation before checking the mission.")

    if st.session_state.get("checked_run_ids", {}).get(mission_id) == result.run_id:
        st.success("This exact run and its explanations have been saved.")
        is_last = mission_id == LAB.missions[-1]
        label = "Continue to final submission" if is_last else "Continue to next mission"
        if st.button(label, type="primary", key=f"continue_{mission_id}"):
            mark_complete(st, mission_id)
            if is_last:
                set_stage(st, "final_submission")
            else:
                st.rerun()

