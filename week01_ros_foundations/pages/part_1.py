from __future__ import annotations

from lab.components import tutorial_component
from lab.navigation import set_stage
from lab.session import response, set_response


def render(st) -> None:
    state = tutorial_component(
        st,
        "robotics_challenges",
        dict(response(st, "part_1.activity", {})),
        key="week01_robotics_challenges",
    )
    set_response(st, "part_1.activity", state)

    complete = all(bool(state.get(item)) for item in ("sensor", "timing", "distributed", "hardware"))
    complete = complete and bool(state.get("changed"))
    st.caption(
        "This is a guided demonstration, not a quiz. Run all four examples and change at least "
        "one condition so you can compare what happens."
    )
    if not complete:
        st.info("Explore each example above; then the next part will unlock.")

    left, right = st.columns(2)
    with left:
        if st.button("Back to welcome", use_container_width=True):
            set_stage(st, "intro")
    with right:
        if st.button("Continue to Part 2", type="primary", disabled=not complete, use_container_width=True):
            set_stage(st, "part_2")
