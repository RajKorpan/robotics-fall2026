from __future__ import annotations

from lab.navigation import set_stage
from simulation.core import simulate_feedback
from simulation.metrics import feedback_metrics
from simulation.plotting import feedback_figure


def render(st) -> None:
    st.title("Interactive playground")
    st.write("Explore freely here. Playground activity is formative and does not pass a mission.")
    gain = st.slider("Gain", 0.1, 5.0, 1.0, 0.1, key="playground_gain")
    disturbance = st.slider("Disturbance", -1.0, 1.0, 0.0, 0.05)
    noise = st.slider("Sensor noise", 0.0, 0.25, 0.0, 0.01)
    trace = simulate_feedback(gain=gain, target=1.0, disturbance=disturbance, sensor_noise=noise)
    st.pyplot(feedback_figure(trace))
    st.json(feedback_metrics(trace))
    if st.button("Start missions", type="primary"):
        set_stage(st, "lab")

