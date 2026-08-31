from __future__ import annotations

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class CommandGuard(Node):
    def __init__(self) -> None:
        super().__init__("course_cmd_vel_guard")
        self.declare_parameter("max_linear", 0.22)
        self.declare_parameter("max_angular", 0.8)
        self.declare_parameter("timeout", 0.5)
        self.max_linear = float(self.get_parameter("max_linear").value)
        self.max_angular = float(self.get_parameter("max_angular").value)
        self.timeout = float(self.get_parameter("timeout").value)
        self.publisher = self.create_publisher(Twist, "/cmd_vel", 10)
        self.subscription = self.create_subscription(Twist, "/student_cmd_vel", self.on_command, 10)
        self.last_command = 0.0
        self.stopped = True
        self.timer = self.create_timer(0.1, self.watchdog)
        self.get_logger().info(
            f"Guard ready: |linear.x| <= {self.max_linear}, "
            f"|angular.z| <= {self.max_angular}, timeout={self.timeout}s"
        )

    def stop(self) -> None:
        self.publisher.publish(Twist())
        self.stopped = True

    def on_command(self, message: Twist) -> None:
        values = (message.linear.x, message.angular.z)
        if not all(math.isfinite(float(value)) for value in values):
            self.get_logger().error("Rejected nonfinite velocity command; stopping")
            self.stop()
            return
        guarded = Twist()
        guarded.linear.x = max(-self.max_linear, min(self.max_linear, float(message.linear.x)))
        guarded.angular.z = max(-self.max_angular, min(self.max_angular, float(message.angular.z)))
        self.publisher.publish(guarded)
        self.last_command = time.monotonic()
        self.stopped = guarded.linear.x == 0.0 and guarded.angular.z == 0.0

    def watchdog(self) -> None:
        if not self.stopped and time.monotonic() - self.last_command > self.timeout:
            self.get_logger().warning("Student command timed out; publishing stop")
            self.stop()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CommandGuard()
    try:
        rclpy.spin(node)
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

