from __future__ import annotations

from lab.components import tutorial_component
from lab.navigation import set_stage
from lab.session import response, set_response


def render(st) -> None:
    state = tutorial_component(
        st,
        "ros_graph_playground",
        dict(response(st, "part_3.activity", {})),
        key="week01_ros_graph_playground",
    )
    set_response(st, "part_3.activity", state)

    complete = all(bool(state.get(item)) for item in ("topic", "service", "failure", "inspect"))
    st.caption(
        "This is a guided demonstration, not a quiz. Follow messages through the graph, compare "
        "a topic with a service, create a failure, and inspect the system."
    )
    if not complete:
        st.info("Complete each graph demonstration to unlock the ROS environment preflight.")

    left, right = st.columns(2)
    with left:
        if st.button("Back to Part 2", use_container_width=True):
            set_stage(st, "part_2")
    with right:
        if st.button("Continue to environment preflight", type="primary", disabled=not complete, use_container_width=True):
            set_stage(st, "preflight")
