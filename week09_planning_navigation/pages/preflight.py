import json
from lab.navigation import set_stage


def render(st):
    st.header("Preflight — establish a reproducible starting state")
    st.code("cd week09_planning_navigation\npython -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\n\nsource /opt/ros/jazzy/setup.bash\nexport TURTLEBOT3_MODEL=burger\ncd ros2_ws && colcon build --symlink-install && cd ..\n./scripts/course_preflight.sh\n./scripts/launch_navigation.sh /absolute/path/to/week06_map.yaml", language="bash")
    st.markdown("In RViz: set the initial pose, confirm `/map`, `/scan`, `/odom`, `/tf`, global costmap, local costmap, plan, and robot model update. Teleoperate briefly; stop before continuing. Record the map path, ROS domain, model, and package check output.")
    output = st.text_area("Paste preflight output", height=160); map_path = st.text_input("Absolute saved-map YAML path")
    ready = "[FAIL]" not in output and output.count("[PASS]") >= 8 and map_path.endswith((".yaml", ".yml"))
    if st.button("Save preflight", disabled=not ready):
        st.session_state["evidence"]["preflight"] = {"ready": True, "map": map_path, "output": output}; st.success("Preflight recorded.")
    if st.session_state["evidence"].get("preflight", {}).get("ready") and st.button("Continue to Mission 1"): set_stage(st, "mission_1")

