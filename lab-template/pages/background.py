from __future__ import annotations

from lab.navigation import set_stage
from lab.session import set_response


def render(st) -> None:
    st.title("Background")
    st.write(
        "The example plant has position and velocity. Its command produces acceleration, "
        "while damping, disturbances, and sensor noise make the response imperfect."
    )
    st.latex(r"u = K(r-y)")
    st.latex(r"\dot{v} = u + d - bv")
    answer = st.text_area(
        "Why must a controller use measured state rather than assume its command succeeded?",
        value=st.session_state.get("responses", {}).get("background_feedback", ""),
        key="background_feedback_widget",
    )
    set_response(st, "background_feedback", answer)
    if st.button("Open playground", type="primary", disabled=not answer.strip()):
        set_stage(st, "playground")

