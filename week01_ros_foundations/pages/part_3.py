from __future__ import annotations

from lab.components import tutorial_component
from lab.navigation import set_stage
from lab.session import response, set_response


def render(st) -> None:
    requirements = {
        "middleware": ("single", "multiple"),
        "communication": ("topic", "service"),
        "failure": ("healthy", "sensor", "type", "visualization"),
        "inspection": ("nodes", "node_info", "topics", "topic_info", "echo", "services", "broken"),
    }
    saved_state = dict(response(st, "part_3.activity", {}))
    received_state = tutorial_component(
        st,
        "ros_graph_playground",
        saved_state,
        key="week01_ros_graph_playground",
    )
    legacy = {
        "middleware": bool(saved_state.get("topic")),
        "communication": bool(saved_state.get("service")),
        "failure": bool(saved_state.get("failure")),
        "inspection": bool(saved_state.get("inspect")),
    }
    state = {}
    for example, observations in requirements.items():
        saved = saved_state.get(example, {})
        received = received_state.get(example, {})
        state[example] = {
            observation: legacy[example]
            or bool(saved.get(observation) if hasattr(saved, "get") else False)
            or bool(received.get(observation) if hasattr(received, "get") else False)
            for observation in observations
        }
    set_response(st, "part_3.activity", state)

    complete = all(
        all(bool(state.get(example, {}).get(observation)) for observation in observations)
        for example, observations in requirements.items()
    )
    if not complete:
        st.info("The progress checklist above shows the next observation to complete.")

    left, right = st.columns(2)
    with left:
        if st.button("Back to Part 2", use_container_width=True):
            set_stage(st, "part_2")
    with right:
        if st.button("Continue to environment preflight", type="primary", disabled=not complete, use_container_width=True):
            set_stage(st, "preflight")
