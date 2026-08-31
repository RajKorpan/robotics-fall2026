# Week 8 — Computer Vision and Learned Perception

An individual ROS 2 and Streamlit lab comparing classical color/contour detection with a frozen pretrained detector, then connecting uncertain perception to bounded robot behavior.

## Learning sequence

1. **Concepts:** trace camera data through perception, decision, and actuation.
2. **Preflight:** verify ROS 2 Jazzy, OpenCV/image packages, the course interfaces, and the frozen detector.
3. **Mission 1 — Classical perception:** tune one HSV/morphology/contour pipeline and evaluate it without condition-specific retuning.
4. **Mission 2 — Learned perception:** inspect detections and sweep confidence thresholds without training a model.
5. **Mission 3 — Perception to action:** search, center, approach, and stop using explicit uncertainty and stale-data fallbacks.
6. **Synthesis:** answer when the robot's apparent visual competence breaks down.

The implementation uses the standard ROS [`sensor_msgs/Image`](https://docs.ros.org/en/ros2_packages/jazzy/api/sensor_msgs/msg/Image.html) interface. ROS documentation recommends `image_transport` for production image streams; the course Python nodes subscribe to raw `sensor_msgs/Image` so the processing logic remains visible, while recorded or compressed transport may be selected outside the node when needed. See the official [`image_transport` documentation](https://docs.ros.org/en/jazzy/p/image_transport/index.html).

## Shared ROS environment

Use the course container configured once in Week 1. It provides ROS 2 Jazzy, OpenCV/NumPy, `cv_bridge`, `image_view`, `image_publisher`, colcon, and Streamlit on Windows, macOS, and Linux. See [`../ROS_DOCKER_SETUP.md`](../ROS_DOCKER_SETUP.md). The instructor still distributes the frozen COCO ONNX model and any required camera rosbag.

## Instructor setup

```bash
sudo apt install ros-jazzy-cv-bridge ros-jazzy-image-view \
  ros-jazzy-image-publisher python3-opencv python3-numpy \
  python3-colcon-common-extensions
cd week08_vision_perception/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
cd ..
python3 -m pip install --user -r requirements.txt
chmod +x scripts/*.sh
```

Place the frozen model at `assets/models/detector.onnx`. Before release, record its source, version, license, input size, class list, and SHA-256 checksum in `assets/models/README.md`. Validate the node against the exact artifact. Do not rely on a classroom-time download.

Generate the deterministic classical condition images:

```bash
python3 scripts/generate_condition_bank.py
```

The instructor should additionally distribute one recorded learned-detector condition run or rosbag so grading remains possible without a camera, GPU, or model download.

## Run the guide

Windows:

```powershell
.\scripts\ros_course.ps1 lab week08_vision_perception
```

macOS/Linux:

```bash
./scripts/ros_course.sh lab week08_vision_perception
```

Then, in the browser desktop terminal:

```bash
bash scripts/course_preflight.sh
```

The guide is at `http://localhost:8501`; the launcher selects `ROS_DOMAIN_ID=28` and sources the Week 8 workspace.

Detector-only mode is the default and does not start behavior:

```bash
bash scripts/launch_pipeline.sh classical /camera/image_raw
bash scripts/launch_pipeline.sh learned /camera/image_raw
```

Behavior must be enabled explicitly and should be used only in simulation:

```bash
bash scripts/launch_pipeline.sh learned /camera/image_raw true
```

## ROS graph

```text
/camera/image_raw
       ↓
classical_detector or learned_detector
       ├── /perception/annotated
       ├── /perception/mask       (classical only)
       └── /perception/target     (TargetObservation)
                    ↓
             target_behavior
                    ↓
           /student_cmd_vel
                    ↓
        course_cmd_vel_guard
                    ↓
               /cmd_vel
```

The behavior stops on stale observations. The independent guard bounds velocity and stops when commands become stale. These layers are separate intentionally: perception confidence is not a motion-safety mechanism.

## Submission

This is an **individual lab**. Submit `student_submission/` and the individual Git commit. The submission includes:

- raw classical and learned condition CSV files;
- checked JSON metrics and threshold sweep;
- representative masks and annotated success/failure images;
- checked behavior scenarios and ROS screenshots/GIFs;
- written explanations and final synthesis; and
- `manifest.json`.

Do not include identifiable images of classmates or bystanders.

## Maintainer checks

```bash
python3 app.py --smoke-test
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
```

ROS integration requires the Jazzy environment:

```bash
cd ros2_ws
colcon build --symlink-install
colcon test
colcon test-result --verbose
```
