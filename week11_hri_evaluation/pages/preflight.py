from pathlib import Path
from lab.navigation import set_stage


def render(st):
    st.header("Protocol and ROS preflight")
    st.markdown("Read `assets/protocol/participant_script.md` aloud before testing. Participation must be voluntary and stoppable. Use a random code such as `P-7K4Q`; never place the participant's name in a filename, note, terminal command, or Git history.")
    st.code("cd week11_hri_evaluation/ros2_ws\nsource /opt/ros/jazzy/setup.bash\ncolcon build --symlink-install\ncd ..\n./scripts/course_preflight.sh\n./scripts/launch_interaction.sh\n\n# In another terminal\nsource /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash\nros2 topic echo /hri/state\nros2 topic echo /hri/display\nros2 topic pub --once /hri/command std_msgs/msg/String \"{data: 'bring the blue cup'}\"\nros2 topic pub --once /hri/command std_msgs/msg/String \"{data: 'yes'}\"\n# Alternate text modality uses the same state machine\nros2 topic pub --once /hri/text_command std_msgs/msg/String \"{data: 'bring the blue cup'}\"\n\n# Test the stop path\nros2 topic pub --once /hri/emergency_stop std_msgs/msg/Bool \"{data: true}\"",language="bash")
    st.info("`/hri/cmd_vel` is intentionally separate from `/cmd_vel`, and `motion_enabled` defaults to false. State, display, and command interaction can therefore be evaluated without moving a robot.")
    output=st.text_area("Paste preflight output",height=160); script=st.checkbox("I read and will follow the participant script"); privacy=st.checkbox("I will collect no identifying, demographic, audio, video, or photo data"); motion=st.checkbox("I confirmed motion_enabled is false")
    ready="[FAIL]" not in output and output.count("[PASS]")>=7 and script and privacy and motion
    if st.button("Save preflight",disabled=not ready): st.session_state["evidence"]["preflight"]={"ready":True,"output":output,"protocol":True,"motion_enabled":False}; st.success("Preflight saved.")
    if st.session_state["evidence"].get("preflight",{}).get("ready") and st.button("Continue to Mission 1"): set_stage(st,"mission_1")
