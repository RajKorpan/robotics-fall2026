from lab.evidence import evidence_id, student_seed
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_2 import evaluate
from simulation.plotting import pipeline_figure
from simulation.scenarios import fusion_dataset, run_pipeline


def render(st):
    st.header("Mission 2 — Filter and fuse")
    st.write("Sensor A updates quickly but is noisy and outlier-prone. Sensor B is steadier and slightly biased, but updates only every fourth time step. Build an estimate that is accurate, available, and responsive when the target moves.")
    seed = student_seed(st.session_state["student"]["course_id"], "mission_2"); dataset = fusion_dataset(seed)
    a, b, c, d = st.columns(4)
    method = a.selectbox("Sensor A filter", ["Raw/hold last", "Moving average", "Median", "Exponential"])
    window = b.slider("Window", 1, 15, 5, 2, disabled=method not in ("Moving average", "Median"))
    alpha = c.slider("Exponential α", 0.05, 1.0, 0.35, 0.05, disabled=method != "Exponential")
    weight = d.slider("Weight on Sensor A", 0.0, 1.0, 0.40, 0.05)
    current = run_pipeline(dataset, method, window, alpha, weight)
    st.pyplot(pipeline_figure(dataset, current))
    st.dataframe([{key: round(value, 4) for key, value in current["metrics"].items()}], hide_index=True, width="stretch")
    st.caption("Lower error and delay are better. Availability is the fraction of time steps with an estimate.")
    if st.button("Record this configuration"):
        attempts = list(st.session_state["mission_2_attempts"])
        signature = current["settings"]
        if not any(item["settings"] == signature for item in attempts): attempts.append({"attempt": len(attempts) + 1, **current})
        st.session_state["mission_2_attempts"] = attempts
    attempts = st.session_state["mission_2_attempts"]
    if attempts:
        st.subheader("Experiment log")
        table = [{"attempt": item["attempt"], **item["settings"], **{key: round(value, 4) for key, value in item["metrics"].items()}} for item in attempts]
        st.dataframe(table, hide_index=True, width="stretch")
        labels = [f"Attempt {item['attempt']}: {item['settings']['method']}" for item in attempts]
        selected = st.selectbox("Configuration to submit", range(len(attempts)), format_func=lambda index: labels[index], key="m2.selected")
    else: selected = -1
    text_response(st, "mission_2.comparison", "Compare moving average and median results. Which error patterns does each handle well?")
    text_response(st, "mission_2.responsiveness", "Explain how your filter settings change smoothing and response delay, using numerical evidence.")
    text_response(st, "mission_2.fusion_choice", "Why is your Sensor A weight reasonable given the strengths and weaknesses of both sensors?")
    if st.button("Check Mission 2", type="primary"):
        check = evaluate(attempts, selected, st.session_state["responses"]); st.session_state["m2.check"] = check
        if check.passed:
            chosen = attempts[selected]; eid = evidence_id("mission_2", attempts, selected); complete_mission(st, "mission_2", eid)
            rows = [{"time_s": t, "truth_m": truth, "sensor_a_m": av, "sensor_b_m": bv, "estimate_m": estimate} for t, truth, av, bv, estimate in zip(dataset["time"], dataset["truth"], dataset["sensor_a"], dataset["sensor_b"], chosen["estimate"])]
            save_mission("mission_2", {"evidence_id": eid, "selected_attempt": selected + 1, "attempts": attempts}, st.session_state["responses"], rows=rows, figure=pipeline_figure(dataset, chosen))
    if st.session_state.get("m2.check"): render_check(st, st.session_state["m2.check"])
    if "mission_2" in st.session_state["completed_missions"] and st.button("Continue to Mission 3"): set_stage(st, "mission_3")
