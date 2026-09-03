from __future__ import annotations

from lab.components import tutorial_component
from lab.navigation import set_stage
from lab.session import response, set_response


def render(st) -> None:
    examples = ("reactive", "behavior", "deliberative", "hybrid", "safety")
    saved_state = dict(response(st, "part_2.activity", {}))
    received_state = tutorial_component(
        st,
        "architecture_playground",
        saved_state,
        key="week01_architecture_playground",
    )
    state = {}
    legacy_modes = saved_state.get("modes", {})
    for example in examples:
        saved = saved_state.get(example, {})
        received = received_state.get(example, {})
        legacy_complete = (
            bool(legacy_modes.get(example)) if example != "safety" and hasattr(legacy_modes, "get")
            else bool(saved_state.get("safety")) if example == "safety"
            else False
        )
        state[example] = {
            flag: legacy_complete
            or bool(saved.get(flag) if hasattr(saved, "get") else False)
            or bool(received.get(flag) if hasattr(received, "get") else False)
            for flag in ("normal", "changed")
        }
    set_response(st, "part_2.activity", state)

    comparisons = [state.get(example, {}) for example in examples]
    complete = all(
        hasattr(comparison, "get")
        and bool(comparison.get("normal"))
        and bool(comparison.get("changed"))
        for comparison in comparisons
    )
    if not complete:
        st.info("The progress checklist above shows the next comparison to run.")

    left, right = st.columns(2)
    with left:
        if st.button("Back to Part 1", use_container_width=True):
            set_stage(st, "part_1")
    with right:
        if st.button("Continue to Part 3", type="primary", disabled=not complete, use_container_width=True):
            set_stage(st, "part_3")
