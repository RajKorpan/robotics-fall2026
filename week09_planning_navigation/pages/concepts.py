from lab.navigation import set_stage


def render(st):
    st.header("System model and evidence")
    st.code("map + localization + goal\n          ↓\n global costmap → planner → path\n                          ↓\n local costmap + sensors → controller → cmd_vel → robot\n                          ↑\n               recovery / replanning\n\n people + course policy → keepout/speed rules → modified costmaps", language="text")
    st.markdown("A **plan** is a geometric proposal; **navigation** is closed-loop execution under sensing and disturbances. Costmaps encode traversability and cost, so changing inflation, keepout, or speed regions changes what the robot treats as acceptable. A failed goal, recovery, near miss, and collision are different outcomes—record them separately.")
    with st.expander("Measurement definitions", expanded=True):
        st.markdown("- Path length: sum of distances between consecutive poses.\n- Clearance: minimum boundary-to-boundary distance; do not substitute center distance.\n- Near miss: a course-defined LiDAR threshold event.\n- Collision: simulator contact when available; the supplied recorder marks a clearly labeled proximity proxy.\n- Success: Nav2 reports completion within the trial limit, not merely that a path existed.")
    if st.button("Continue to preflight"): set_stage(st, "preflight")

