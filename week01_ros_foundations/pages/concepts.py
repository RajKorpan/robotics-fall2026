from __future__ import annotations

from lab.navigation import set_stage
from lab.ui import choice_response, text_response


def render(st) -> None:
    st.title("A robot is an interacting system")
    st.markdown(
        "ROS 2 organizes robot software into **nodes**. Nodes exchange structured "
        "**messages** through named **topics**. Publishers produce messages and subscribers receive them."
    )
    st.code(
        "LiDAR → sensor node → /scan → behavior node\n"
        "behavior node → /student_cmd_vel → safety guard → /cmd_vel → simulated robot"
    )
    st.subheader("Commit your predictions before observing the real system")
    answers = [
        text_response(st, "concept.sensor_information", "What information must pass from a sensor to a behavior node?"),
        text_response(st, "concept.command_information", "What information must pass from a behavior node to the motion controller?"),
        choice_response(st, "concept.rviz_closes", "If RViz closes, should the robot necessarily stop?", ["Yes", "No", "It depends on RViz's graph connections"]),
        text_response(st, "concept.sensor_stops", "What should a safe behavior do if sensor messages stop arriving?"),
        text_response(st, "concept.robot_definition", "Which pieces together make up the robot system in this lab?"),
    ]
    if st.button("Lock predictions and continue", type="primary", disabled=not all(str(answer).strip() for answer in answers)):
        st.session_state["concept_predictions_locked"] = True
        set_stage(st, "preflight")

