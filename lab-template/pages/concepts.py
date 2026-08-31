from __future__ import annotations

from lab.navigation import set_stage
from lab.session import set_response


def render(st) -> None:
    st.title("Concepts")
    st.write(
        "A feedback controller repeatedly measures the system, compares the measurement "
        "with a target, and uses the error to choose a corrective command."
    )
    st.code("error = target - measurement\ncommand = gain * error")
    answer = st.text_area(
        "Prediction: what could happen if the gain is much too large?",
        value=st.session_state.get("responses", {}).get("concept_gain_prediction", ""),
        key="concept_gain_prediction_widget",
    )
    set_response(st, "concept_gain_prediction", answer)
    if st.button("Continue", type="primary", disabled=not answer.strip()):
        set_stage(st, "background")

