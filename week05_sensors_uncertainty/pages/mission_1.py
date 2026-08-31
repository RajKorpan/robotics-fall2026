from lab.evidence import evidence_id, student_seed
from lab.navigation import set_stage
from lab.session import complete_mission, response, set_response
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_1 import evaluate
from simulation.plotting import sample_figure
from simulation.sensors import profile_for_seed, sample_metrics, static_samples


def render(st):
    st.header("Mission 1 — Characterize an imperfect sensor")
    st.write("A stationary target is exactly **2.00 m** away. Analyze 240 samples from your assigned sensor. Compute sample variance using the `n−1` denominator. Count a value as an outlier when it differs from the median by more than the larger of 0.30 m or three robust standard deviations (`1.4826 × MAD`). Diagnose the dominant imperfection from evidence—not from a single unusual point.")
    seed = student_seed(st.session_state["student"]["course_id"], "mission_1")
    profile_name, config = profile_for_seed(seed); samples = static_samples(2.0, 240, config, seed)
    metrics = sample_metrics(samples, 2.0); figure = sample_figure(samples, 2.0)
    st.pyplot(figure)
    rows = [{"sample": i, "measurement_m": value, "valid": value is not None} for i, value in enumerate(samples)]
    import pandas as pd
    st.download_button("Download measurements.csv", pd.DataFrame(rows).to_csv(index=False), "mission1_measurements.csv", "text/csv")
    cols = st.columns(3)
    fields = (("mean", "Mean (m)"), ("variance", "Variance (m²)"), ("bias", "Bias (m)"), ("median", "Median (m)"), ("dropouts", "Dropout count"), ("outliers", "Outlier count"))
    for index, (key, label) in enumerate(fields):
        value = cols[index % 3].text_input(label, str(response(st, f"mission_1.{key}", "")), key=f"m1.{key}"); set_response(st, f"mission_1.{key}", value)
    selected = st.selectbox("Dominant imperfection", ["Choose…", "biased", "noisy", "quantized", "outlier_prone"], index=max(0, ["Choose…", "biased", "noisy", "quantized", "outlier_prone"].index(response(st, "mission_1.profile", "Choose…"))))
    set_response(st, "mission_1.profile", selected)
    text_response(st, "mission_1.bias_vs_variance", "Use your results to explain why bias and variance describe different failures.")
    text_response(st, "mission_1.more_samples", "Would collecting more samples remove this sensor's main problem? Why or why not?")
    text_response(st, "mission_1.robot_consequence", "Give one robot decision this imperfection could change and explain the consequence.")
    if st.button("Check Mission 1", type="primary"):
        check = evaluate(metrics, profile_name, st.session_state["responses"]); st.session_state["m1.check"] = check
        if check.passed:
            eid = evidence_id("mission_1", {"seed": seed, "metrics": metrics, "profile": profile_name}); complete_mission(st, "mission_1", eid)
            save_mission("mission_1", {"evidence_id": eid, "metrics": metrics, "profile": profile_name}, st.session_state["responses"], rows=rows, figure=figure)
    if st.session_state.get("m1.check"): render_check(st, st.session_state["m1.check"])
    if "mission_1" in st.session_state["completed_missions"] and st.button("Continue to Mission 2"): set_stage(st, "mission_2")
