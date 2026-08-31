from __future__ import annotations

from lab.evidence import preflight_result
from lab.navigation import set_stage


def render(st) -> None:
    st.title("Environment preflight")
    st.write("Setup is a prerequisite, not the graded activity. Run the check before launching the simulator.")
    st.code("./scripts/course_preflight.sh", language="bash")
    result = preflight_result()
    checks = result.get("checks", [])
    if checks:
        st.dataframe(checks, hide_index=True, width="stretch")
        ready = all(check.get("passed") for check in checks)
        if ready:
            st.success("Environment ready.")
        else:
            st.error("Resolve the failed setup checks or ask the instructor/TA for help.")
    else:
        ready = False
        st.info("No preflight evidence found yet. Run the command, then refresh this page.")
    with st.expander("What the preflight checks"):
        st.markdown(
            "ROS 2 Jazzy, workspace and packages, TurtleBot3 model, command guard, "
            "evidence directory, ROS domain ID, and stale simulator processes."
        )
    if st.button("Refresh evidence"):
        st.rerun()
    if st.button("Continue to Mission 1", type="primary", disabled=not ready):
        set_stage(st, "mission_1")

