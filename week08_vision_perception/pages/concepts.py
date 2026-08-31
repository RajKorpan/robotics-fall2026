from lab.navigation import set_stage
from lab.ui import text_response
def render(st):
    st.header("Seeing is a system behavior")
    st.code("sensor_msgs/Image\n        ↓\nclassical or learned detector\n        ↓\nTargetObservation\n        ↓\ndecision node\n        ↓\n/student_cmd_vel → independent guard → /cmd_vel",language=None)
    st.markdown("A classical detector makes assumptions explicit: color range, morphology, contour area, and geometry. A learned detector hides more of its prior knowledge in frozen weights and exposes outputs such as class, box, and confidence. Neither directly observes truth. A downstream robot must treat both as uncertain, time-dependent evidence.")
    st.markdown("**Precision** asks how often positive detections are correct. **Recall** asks how often real targets are found. Raising a confidence threshold often improves precision while reducing recall. The appropriate balance depends on what the robot does after a detection.")
    text_response(st,"concepts.prediction","Predict how dim light, glare, distance, occlusion, rotation, clutter, and a similar-looking distractor will affect classical and learned perception differently.")
    if st.button("Continue to preflight",type="primary"):set_stage(st,"preflight")
