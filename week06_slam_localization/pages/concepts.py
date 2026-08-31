from lab.navigation import set_stage
from lab.ui import text_response
def render(st):
    st.header("From measurements to a map—and back to a pose")
    st.markdown("""
SLAM jointly estimates a map and the robot trajectory. The robot receives a LiDAR scan in `base_scan`, motion information through `odom → base_link`, and uses scan matching to estimate `map → odom`. The composed transform answers where the robot is in the map.

An occupancy grid stores cells as free, occupied, or unknown. It is an estimate shaped by the route, viewpoints, sensor limits, motion, and accumulated error. Revisiting a recognized place can create a **loop closure**, allowing the SLAM system to revise earlier trajectory and map estimates.

Localization reverses the emphasis: the map is fixed, while AMCL maintains a distribution over possible robot poses. A single displayed arrow is not proof that the estimate is correct; covariance, consistency with scans, recovery behavior, and downstream navigation performance are all relevant evidence.
""")
    st.subheader("System relationship")
    st.code("LiDAR + odometry + TF → SLAM → occupancy map + map→odom\nsaved map + LiDAR + odometry + initial pose → AMCL → pose distribution", language=None)
    text_response(st, "concepts.prediction", "Predict one symptom of poor odometry and one symptom of weak scan geometry. Which ROS displays or topics would help distinguish them?")
    if st.button("Continue to preflight", type="primary"): set_stage(st, "preflight")
