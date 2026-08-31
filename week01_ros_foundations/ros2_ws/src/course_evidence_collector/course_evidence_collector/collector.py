from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


def evidence_directory() -> Path:
    configured = os.environ.get("WEEK01_EVIDENCE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    root = Path.cwd().parent if Path.cwd().name == "ros2_ws" else Path.cwd()
    return root / "runtime" / "evidence"


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


class EvidenceCollector(Node):
    def __init__(self) -> None:
        super().__init__("course_evidence_collector")
        self.output = evidence_directory()
        self.latest_scan = None
        self.latest_odom = None
        self.latest_command = None
        self.create_subscription(LaserScan, "/scan", self.on_scan, 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(Twist, "/student_cmd_vel", self.on_command, 10)
        self.timer = self.create_timer(2.0, self.snapshot)
        self.get_logger().info(f"Writing evidence to {self.output}")

    def on_scan(self, message: LaserScan) -> None:
        finite = [float(value) for value in message.ranges if value == value and value not in (float("inf"), float("-inf"))]
        self.latest_scan = {
            "frame_id": message.header.frame_id,
            "angle_min": message.angle_min,
            "angle_max": message.angle_max,
            "angle_increment": message.angle_increment,
            "sample_count": len(message.ranges),
            "finite_count": len(finite),
            "minimum_finite_range": min(finite) if finite else None,
        }

    def on_odom(self, message: Odometry) -> None:
        self.latest_odom = {
            "frame_id": message.header.frame_id,
            "child_frame_id": message.child_frame_id,
            "position": {
                "x": message.pose.pose.position.x,
                "y": message.pose.pose.position.y,
            },
            "orientation": {
                "x": message.pose.pose.orientation.x,
                "y": message.pose.pose.orientation.y,
                "z": message.pose.pose.orientation.z,
                "w": message.pose.pose.orientation.w,
            },
            "linear_x": message.twist.twist.linear.x,
            "angular_z": message.twist.twist.angular.z,
        }

    def on_command(self, message: Twist) -> None:
        self.latest_command = {"linear_x": message.linear.x, "angular_z": message.angular.z}

    def snapshot(self) -> None:
        nodes = []
        for name, namespace in self.get_node_names_and_namespaces():
            full_name = f"{namespace.rstrip('/')}/{name}" if namespace != "/" else f"/{name}"
            nodes.append({"name": full_name})
        topics = [
            {"name": name, "types": list(types)}
            for name, types in self.get_topic_names_and_types()
        ]
        payload = {
            "schema_version": 1,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "nodes": sorted(nodes, key=lambda value: value["name"]),
            "topics": sorted(topics, key=lambda value: value["name"]),
            "samples": {
                "/scan": self.latest_scan,
                "/odom": self.latest_odom,
                "/student_cmd_vel": self.latest_command,
            },
        }
        atomic_json(self.output / "graph_snapshot.json", payload)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = EvidenceCollector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

