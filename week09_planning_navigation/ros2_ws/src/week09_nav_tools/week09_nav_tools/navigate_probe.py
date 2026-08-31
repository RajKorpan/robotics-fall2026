from __future__ import annotations

from math import cos, hypot, isfinite, sin
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from week09_nav_tools.io import append_row


class NavigateProbe(Node):
    def __init__(self):
        super().__init__("week09_navigate_probe")
        defaults = (("trial_id", "trial"), ("condition", "open"), ("goal_x", 0.0), ("goal_y", 0.0), ("goal_yaw", 0.0), ("output", "runtime/evidence/navigation.json"), ("near_miss_range_m", 0.25), ("collision_proxy_range_m", 0.12))
        for name, default in defaults: self.declare_parameter(name, default)
        self.client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.create_subscription(Odometry, "/odom", self.on_odom, 20)
        self.create_subscription(LaserScan, "/scan", self.on_scan, 20)
        self.previous = None; self.distance = 0.0; self.minimum_scan = None
        self.near_miss = False; self.collision_proxy = False; self.recoveries = 0

    def on_odom(self, msg):
        point = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        if self.previous is not None: self.distance += hypot(point[0]-self.previous[0], point[1]-self.previous[1])
        self.previous = point

    def on_scan(self, msg):
        valid = [r for r in msg.ranges if isfinite(r) and msg.range_min <= r <= msg.range_max]
        if not valid: return
        current = min(valid); self.minimum_scan = current if self.minimum_scan is None else min(self.minimum_scan, current)
        self.near_miss |= current < float(self.get_parameter("near_miss_range_m").value)
        self.collision_proxy |= current < float(self.get_parameter("collision_proxy_range_m").value)

    def feedback(self, message): self.recoveries = max(self.recoveries, int(message.feedback.number_of_recoveries))

    def run(self):
        goal = NavigateToPose.Goal(); goal.pose = PoseStamped(); goal.pose.header.frame_id = "map"; goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(self.get_parameter("goal_x").value); goal.pose.pose.position.y = float(self.get_parameter("goal_y").value)
        yaw = float(self.get_parameter("goal_yaw").value); goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = sin(yaw/2), cos(yaw/2)
        if not self.client.wait_for_server(timeout_sec=15.0): raise RuntimeError("navigate_to_pose action server unavailable")
        started = time.monotonic(); future = self.client.send_goal_async(goal, feedback_callback=self.feedback); rclpy.spin_until_future_complete(self, future)
        handle = future.result()
        if not handle.accepted: self.write("rejected", started); return
        result = handle.get_result_async(); rclpy.spin_until_future_complete(self, result)
        self.write("succeeded" if result.result().status == GoalStatus.STATUS_SUCCEEDED else "failed", started)

    def write(self, status, started):
        row = {"trial_id": str(self.get_parameter("trial_id").value), "condition": str(self.get_parameter("condition").value), "status": status, "completion_time_s": round(time.monotonic()-started, 3), "path_length_m": round(self.distance, 3), "minimum_scan_range_m": None if self.minimum_scan is None else round(self.minimum_scan, 3), "collision_events": int(self.collision_proxy), "near_miss_events": int(self.near_miss), "recovery_count": self.recoveries, "measurement_note": "collision_events is a LiDAR proximity proxy; record simulator contact separately if available"}
        append_row(str(self.get_parameter("output").value), row); self.get_logger().info(str(row))


def main():
    rclpy.init(); node = NavigateProbe()
    try: node.run()
    finally: node.destroy_node(); rclpy.shutdown()

