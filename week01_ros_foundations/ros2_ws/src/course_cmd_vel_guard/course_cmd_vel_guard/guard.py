from __future__ import annotations

import math
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node


def bounded_values(linear_x: float, angular_z: float, max_linear: float, max_angular: float) -> tuple[float, float]:
    values = (float(linear_x), float(angular_z))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Velocity values must be finite")
    return (
        max(-max_linear, min(max_linear, values[0])),
        max(-max_angular, min(max_angular, values[1])),
    )


class CommandGuard(Node):
    def __init__(self) -> None:
        super().__init__("course_cmd_vel_guard")
        self.declare_parameter("max_linear", 0.22)
        self.declare_parameter("max_angular", 0.8)
        self.declare_parameter("timeout", 0.5)
        self.max_linear = float(self.get_parameter("max_linear").value)
        self.max_angular = float(self.get_parameter("max_angular").value)
        self.timeout = float(self.get_parameter("timeout").value)
        self.publisher = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.subscription = self.create_subscription(Twist, "/student_cmd_vel", self.on_command, 10)
        self.last_command = 0.0
        self.stopped = True
        self.timer = self.create_timer(0.1, self.watchdog)
        self.get_logger().info(
            f"Guard ready: |linear.x| <= {self.max_linear}, "
            f"|angular.z| <= {self.max_angular}, timeout={self.timeout}s"
        )

    def stop(self) -> None:
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(message)
        self.stopped = True

    def on_command(self, message: Twist) -> None:
        try:
            linear_x, angular_z = bounded_values(
                message.linear.x,
                message.angular.z,
                self.max_linear,
                self.max_angular,
            )
        except ValueError:
            self.get_logger().error("Rejected nonfinite velocity command; stopping")
            self.stop()
            return
        guarded = TwistStamped()
        guarded.header.stamp = self.get_clock().now().to_msg()
        guarded.twist.linear.x = linear_x
        guarded.twist.angular.z = angular_z
        self.publisher.publish(guarded)
        self.last_command = time.monotonic()
        self.stopped = guarded.twist.linear.x == 0.0 and guarded.twist.angular.z == 0.0

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
