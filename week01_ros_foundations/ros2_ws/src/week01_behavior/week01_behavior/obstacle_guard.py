from __future__ import annotations

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from week01_behavior.decision import decide_velocity, front_distance


class ObstacleGuard(Node):
    """Starter ROS wrapper. Students implement the pure functions in decision.py."""

    def __init__(self) -> None:
        super().__init__("obstacle_guard")
        self.declare_parameter("front_half_width_degrees", 15.0)
        self.declare_parameter("stop_distance", 0.5)
        self.declare_parameter("forward_speed", 0.08)
        self.declare_parameter("scan_timeout", 0.5)
        self.half_width = math.radians(float(self.get_parameter("front_half_width_degrees").value))
        self.stop_distance = float(self.get_parameter("stop_distance").value)
        self.forward_speed = min(0.18, max(0.0, float(self.get_parameter("forward_speed").value)))
        self.scan_timeout = float(self.get_parameter("scan_timeout").value)
        self.publisher = self.create_publisher(Twist, "/student_cmd_vel", 10)
        self.create_subscription(LaserScan, "/scan", self.on_scan, 10)
        self.last_scan_at = 0.0
        self.timer = self.create_timer(0.1, self.watchdog)

    def publish_speed(self, speed: float) -> None:
        message = Twist()
        message.linear.x = min(self.forward_speed, max(0.0, float(speed)))
        self.publisher.publish(message)

    def on_scan(self, message: LaserScan) -> None:
        distance = front_distance(
            message.ranges,
            message.angle_min,
            message.angle_increment,
            self.half_width,
        )
        speed = decide_velocity(distance, self.stop_distance, self.forward_speed)
        self.publish_speed(speed)
        self.last_scan_at = time.monotonic()

    def watchdog(self) -> None:
        if time.monotonic() - self.last_scan_at > self.scan_timeout:
            self.publish_speed(0.0)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ObstacleGuard()
    try:
        rclpy.spin(node)
    finally:
        node.publish_speed(0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

