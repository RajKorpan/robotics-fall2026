from __future__ import annotations

from lab.evidence import preflight_result
from lab.navigation import set_stage


def render(st) -> None:
    st.title("Environment preflight")
    st.write("Week 1 uses the shared course container that will also support Weeks 3, 6, 8, 9, and 11. Complete the one-time host setup in `ROS_DOCKER_SETUP.md`, start this lab with the course launcher, then run the check below in the browser desktop terminal.")
    st.code("bash scripts/course_preflight.sh", language="bash")
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
    with st.expander("One-time cross-platform setup"):
        st.markdown(
            "**Windows:** `powershell -ExecutionPolicy Bypass -File .\\scripts\\ros_course.ps1 setup`  \n"
            "**macOS/Linux:** `./scripts/ros_course.sh setup`  \n\n"
            "Run these from the repository root on the host, not inside this terminal. "
            "They build one Ubuntu/ROS 2 Jazzy image and all six ROS workspaces."
        )
    if st.button("Refresh evidence"):
        st.rerun()
    if st.button("Continue to Mission 1", type="primary", disabled=not ready):
        set_stage(st, "mission_1")
