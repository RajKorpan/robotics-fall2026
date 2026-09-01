from __future__ import annotations

from lab.components import tutorial_component
from lab.navigation import set_stage
from lab.session import response, set_response


def render(st) -> None:
    state = tutorial_component(
        st,
        "architecture_playground",
        dict(response(st, "part_2.activity", {})),
        key="week01_architecture_playground",
    )
    set_response(st, "part_2.activity", state)

    explored_modes = state.get("modes", {})
    complete = all(bool(explored_modes.get(mode)) for mode in ("reactive", "behavior", "deliberative", "hybrid"))
    complete = complete and bool(state.get("safety"))
    st.caption(
        "This is a guided demonstration, not a quiz. Compare all four architectures and run "
        "the safety-override example."
    )
    if not complete:
        st.info("Explore every architecture and the safety example to continue.")

    left, right = st.columns(2)
    with left:
        if st.button("Back to Part 1", use_container_width=True):
            set_stage(st, "part_1")
    with right:
        if st.button("Continue to Part 3", type="primary", disabled=not complete, use_container_width=True):
            set_stage(st, "part_3")
