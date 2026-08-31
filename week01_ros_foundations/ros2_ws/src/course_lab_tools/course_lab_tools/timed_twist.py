from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


def evidence_directory() -> Path:
    configured = os.environ.get("WEEK01_EVIDENCE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    root = Path.cwd().parent if Path.cwd().name == "ros2_ws" else Path.cwd()
    return root / "runtime" / "evidence"


def yaw_from_quaternion(orientation) -> float:
    siny = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
    cosy = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
    return math.atan2(siny, cosy)


class TimedTwist(Node):
    def __init__(self) -> None:
        super().__init__("timed_twist_trial")
        self.declare_parameter("trial_type", "student_trial")
        self.declare_parameter("linear_x", 0.0)
        self.declare_parameter("angular_z", 0.0)
        self.declare_parameter("duration", 1.0)
        self.trial_type = str(self.get_parameter("trial_type").value)
        self.linear_x = float(self.get_parameter("linear_x").value)
        self.angular_z = float(self.get_parameter("angular_z").value)
        self.duration = max(0.1, float(self.get_parameter("duration").value))
        if abs(self.linear_x) > 0.22 or abs(self.angular_z) > 0.8:
            raise ValueError("Requested command exceeds course limits")
        self.publisher = self.create_publisher(Twist, "/student_cmd_vel", 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.timer = self.create_timer(0.05, self.tick)
        self.latest_pose = None
        self.start_pose = None
        self.end_pose = None
        self.started_at = None
        self.done = False
        self.stop_sent = False

    def on_odom(self, message: Odometry) -> None:
        self.latest_pose = {
            "x": message.pose.pose.position.x,
            "y": message.pose.pose.position.y,
            "theta": yaw_from_quaternion(message.pose.pose.orientation),
        }

    def tick(self) -> None:
        if self.latest_pose is None:
            return
        if self.started_at is None:
            self.started_at = time.monotonic()
            self.start_pose = dict(self.latest_pose)
            self.get_logger().info(f"Starting {self.trial_type} for {self.duration:.2f}s")
        elapsed = time.monotonic() - self.started_at
        if elapsed < self.duration:
            message = Twist()
            message.linear.x = self.linear_x
            message.angular.z = self.angular_z
            self.publisher.publish(message)
            return
        self.publisher.publish(Twist())
        self.stop_sent = True
        self.end_pose = dict(self.latest_pose)
        self.done = True

    def result(self) -> dict:
        start = self.start_pose or {"x": 0.0, "y": 0.0, "theta": 0.0}
        end = self.end_pose or self.latest_pose or start
        return {
            "trial_type": self.trial_type,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "linear_x": self.linear_x,
            "angular_z": self.angular_z,
            "duration": self.duration,
            "start_pose": start,
            "end_pose": end,
            "displacement": math.hypot(end["x"] - start["x"], end["y"] - start["y"]),
            "heading_change": math.atan2(math.sin(end["theta"] - start["theta"]), math.cos(end["theta"] - start["theta"])),
            "completed": self.done,
            "stop_sent": self.stop_sent,
        }


def append_result(result: dict) -> Path:
    path = evidence_directory() / "motion_trials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        trials = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except json.JSONDecodeError:
        trials = []
    trials = [trial for trial in trials if trial.get("trial_type") != result["trial_type"]]
    trials.append(result)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(trials, indent=2), encoding="utf-8")
    temporary.replace(path)
    return path


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TimedTwist()
    try:
        deadline = time.monotonic() + node.duration + 10.0
        while rclpy.ok() and not node.done and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        node.publisher.publish(Twist())
        if not node.done:
            raise RuntimeError("No odometry received or trial timed out")
        path = append_result(node.result())
        node.get_logger().info(f"Saved trial to {path}")
    finally:
        node.publisher.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

