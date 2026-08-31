import json
from lab.navigation import set_stage


def render(st):
    st.header("Preflight — establish a reproducible starting state")
    st.write("Use the shared course container configured in Week 1. The launcher selects `ROS_DOMAIN_ID=29`, the TurtleBot3 model, and the Week 9 workspace.")
    st.code("bash scripts/course_preflight.sh\nbash scripts/launch_navigation.sh /workspace/week06_slam_localization/student_submission/path/to/map.yaml", language="bash")
    st.markdown("In RViz: set the initial pose, confirm `/map`, `/scan`, `/odom`, `/tf`, global costmap, local costmap, plan, and robot model update. Teleoperate briefly; stop before continuing. Record the map path, ROS domain, model, and package check output.")
    output = st.text_area("Paste preflight output", height=160); map_path = st.text_input("Absolute saved-map YAML path")
    ready = "[FAIL]" not in output and output.count("[PASS]") >= 8 and map_path.endswith((".yaml", ".yml"))
    if st.button("Save preflight", disabled=not ready):
        st.session_state["evidence"]["preflight"] = {"ready": True, "map": map_path, "output": output}; st.success("Preflight recorded.")
    if st.session_state["evidence"].get("preflight", {}).get("ready") and st.button("Continue to Mission 1"): set_stage(st, "mission_1")
