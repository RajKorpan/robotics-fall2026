from __future__ import annotations

from lab.navigation import set_stage
from lab.session import response, set_response
from lab.ui import choice_response, text_response


ARCHITECTURES = ["Reactive", "Behavior-based", "Deliberative", "Hybrid"]


def render(st) -> None:
    st.title("Part 2: Robot software architectures")
    st.write(
        "An architecture breaks a robot into components and defines how they interact. "
        "Every architecture balances fast reaction, long-range reasoning, predictability, "
        "computational cost, and dependence on an accurate model."
    )

    st.subheader("Sense, decide, and act")
    st.code(
        "environment → sensors → decision/control → actuators → environment\n"
        "                         ↑\n"
        "               safety may override"
    )
    pipeline = {
        "sense": choice_response(st, "part_2.pipeline.scan", "A LiDAR scan belongs primarily to", ["Sense", "Decide", "Act"]),
        "decide": choice_response(st, "part_2.pipeline.threshold", "Comparing a range with a stop threshold belongs primarily to", ["Sense", "Decide", "Act"]),
        "act": choice_response(st, "part_2.pipeline.motor", "Applying wheel velocity belongs primarily to", ["Sense", "Decide", "Act"]),
    }

    st.subheader("Architecture spectrum")
    st.markdown(
        "| Architecture | Organizing idea | Strength | Important limitation |\n"
        "|---|---|---|---|\n"
        "| Reactive | Stimulus directly selects a response | Fast and simple | Little memory or foresight |\n"
        "| Behavior-based | Several small behaviors are coordinated | Flexible in dynamic settings | Arbitration can be difficult to predict |\n"
        "| Deliberative | A world model supports planning | Reasons about goals and consequences | Model may be wrong and planning may be slow |\n"
        "| Hybrid | Deliberative, executive, and reactive layers cooperate | Planning with local reaction | More interfaces and failure paths |"
    )
    knowledge = {
        "hazard": choice_response(st, "part_2.knowledge.hazard", "Which style best fits an immediate collision-avoidance rule?", ARCHITECTURES),
        "model": choice_response(st, "part_2.knowledge.model", "Which style depends most directly on a world model and action sequence?", ARCHITECTURES),
        "combined": choice_response(st, "part_2.knowledge.combined", "Which style explicitly combines slower planning with fast local reaction?", ARCHITECTURES),
    }

    st.subheader("Apply the trade-offs")
    st.caption("These scenarios can support nuanced choices. Your justification matters.")
    scenarios = dict(response(st, "part_2.scenarios", {}))
    for key, label in (
        ("emergency", "Emergency collision avoidance"),
        ("chess", "A chess-playing robot"),
        ("delivery", "An autonomous hospital delivery robot"),
        ("vacuum", "A robot vacuum"),
    ):
        values = ["Select an architecture", *ARCHITECTURES]
        prior = scenarios.get(key, values[0])
        selected = st.selectbox(
            label, values, index=values.index(prior) if prior in values else 0,
            key=f"widget.part_2.scenario.{key}",
        )
        scenarios[key] = "" if selected == values[0] else selected
    set_response(st, "part_2.scenarios", scenarios)
    scenario_reasoning = text_response(
        st,
        "part_2.scenario_reasoning",
        "Choose two scenarios and justify the architectures using reaction time, world models, planning, or coordination.",
        height=150,
    )
    hospital_failure = text_response(
        st,
        "part_2.hospital_failure",
        "For a hospital delivery robot, which failure is most concerning—getting lost, being slow, blocking a hallway, or contacting a person—and how should architecture reduce it?",
        height=140,
    )

    st.subheader("Layered safety")
    safety_order = choice_response(
        st,
        "part_2.safety_order",
        "Which ordering gives a local safety mechanism the final opportunity to override motion?",
        [
            "Sensors → goal planner → controller → safety override → actuators",
            "Safety override → goal planner → controller → actuators",
            "Controller → actuators → safety override → sensors",
        ],
    )
    arbitration = text_response(
        st,
        "part_2.arbitration",
        "If wander, follow-goal, and avoid-obstacle behaviors request different motions, what must an arbitrator decide?",
    )
    lab_prediction = choice_response(
        st,
        "part_2.lab_prediction",
        "The Week 1 rule 'if an obstacle is close, stop; otherwise move slowly' is primarily",
        ARCHITECTURES,
    )
    limitation = text_response(
        st,
        "part_2.reactive_limitation",
        "Predict one limitation of that architecture and one layer a more capable future robot might add.",
    )

    facts_correct = (
        pipeline == {"sense": "Sense", "decide": "Decide", "act": "Act"}
        and knowledge == {"hazard": "Reactive", "model": "Deliberative", "combined": "Hybrid"}
        and safety_order == "Sensors → goal planner → controller → safety override → actuators"
        and lab_prediction == "Reactive"
    )
    written_complete = all(
        len(value.strip()) >= 60
        for value in (scenario_reasoning, hospital_failure, arbitration, limitation)
    )
    scenarios_complete = all(scenarios.values())
    if any(pipeline.values()) or any(knowledge.values()) or safety_order or lab_prediction:
        if not facts_correct:
            st.warning("Revisit the definitions above: separate sensing, deciding, and acting, then compare reaction with planning.")
    if st.button(
        "Continue to Part 3",
        type="primary",
        disabled=not (facts_correct and written_complete and scenarios_complete),
    ):
        set_stage(st, "part_3")
