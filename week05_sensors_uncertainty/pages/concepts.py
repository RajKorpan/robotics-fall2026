from lab.evidence import student_seed
from lab.navigation import set_stage
from lab.ui import text_response
from simulation.plotting import sample_figure
from simulation.sensors import SensorConfig, sample_metrics, static_samples


def render(st):
    st.header("Sensor playground")
    st.write("Change one property at a time. The dashed line is the true 2.0 m distance; missing points are dropouts.")
    col1, col2, col3 = st.columns(3)
    noise = col1.slider("Noise σ (m)", 0.0, 0.40, 0.08, 0.01)
    bias = col2.slider("Bias (m)", -0.40, 0.40, 0.0, 0.01)
    resolution = col3.select_slider("Resolution (m)", options=[0.001, 0.01, 0.05, 0.10, 0.25], value=0.01)
    dropout = col1.slider("Dropout probability", 0.0, 0.40, 0.02, 0.01)
    outliers = col2.slider("Outlier probability", 0.0, 0.25, 0.02, 0.01)
    false_detection = col3.slider("False-detection probability", 0.0, 0.20, 0.0, 0.01)
    config = SensorConfig(noise_std=noise, bias=bias, resolution=resolution, dropout_rate=dropout, outlier_rate=outliers, outlier_scale=1.2, false_detection_rate=false_detection)
    samples = static_samples(2.0, 180, config, student_seed(st.session_state["student"]["course_id"], "playground"))
    st.pyplot(sample_figure(samples, 2.0))
    st.dataframe([sample_metrics(samples, 2.0)], hide_index=True, width="stretch")
    text_response(st, "concepts.observation", "What changed when you increased noise versus bias? Refer to the plot and at least two statistics.")
    if st.button("Continue to Mission 1", type="primary"): set_stage(st, "mission_1")
