from __future__ import annotations

import math

from lab.navigation import set_stage
from lab.ui import text_response
from simulation.kinematics import Segment, integrate_sequence


def render(st) -> None:
    st.title("From velocity to pose")
    st.write("For planar motion, linear and angular velocity determine how pose changes over time.")
    st.latex(r"\dot{x}=v\cos\theta,\quad \dot{y}=v\sin\theta,\quad \dot{\theta}=\omega")
    col1, col2, col3 = st.columns(3)
    with col1:
        linear = st.slider("Linear velocity v", -0.2, 0.2, 0.12, 0.01)
    with col2:
        angular = st.slider("Angular velocity ω", -0.8, 0.8, 0.3, 0.05)
    with col3:
        duration = st.slider("Duration", 0.5, 6.0, 3.0, 0.5)
    pose = integrate_sequence((Segment(linear, angular, duration),))
    st.metric("Predicted x", f"{pose['x']:.3f} m")
    st.metric("Predicted y", f"{pose['y']:.3f} m")
    st.metric("Predicted heading", f"{math.degrees(pose['theta']):.1f}°")
    answers = [
        text_response(st, "concept.velocity_pose", "Why does a velocity command require a duration to predict pose?"),
        text_response(st, "concept.arc", "Why does nonzero linear and angular velocity produce an arc?"),
        text_response(st, "concept.model_limits", "Name one assumption in this motion model that a robot may violate."),
    ]
    if st.button("Continue", type="primary", disabled=not all(answer.strip() for answer in answers)):
        set_stage(st, "preflight")

