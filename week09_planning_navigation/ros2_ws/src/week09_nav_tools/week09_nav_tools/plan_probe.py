from __future__ import annotations

from math import atan2, cos, hypot, sin
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient
from rclpy.node import Node

from week09_nav_tools.io import append_row


class PlanProbe(Node):
    def __init__(self):
        super().__init__("week09_plan_probe")
        for name, default in (("goal_id", "goal"), ("goal_x", 0.0), ("goal_y", 0.0), ("goal_yaw", 0.0), ("expected_reachable", True), ("output", "runtime/evidence/plans.json")):
            self.declare_parameter(name, default)
        self.client = ActionClient(self, ComputePathToPose, "compute_path_to_pose")

    def run(self):
        goal = ComputePathToPose.Goal()
        goal.goal = PoseStamped()
        goal.goal.header.frame_id = "map"
        goal.goal.header.stamp = self.get_clock().now().to_msg()
        goal.goal.pose.position.x = float(self.get_parameter("goal_x").value)
        goal.goal.pose.position.y = float(self.get_parameter("goal_y").value)
        yaw = float(self.get_parameter("goal_yaw").value)
        goal.goal.pose.orientation.z, goal.goal.pose.orientation.w = sin(yaw / 2), cos(yaw / 2)
        goal.use_start = False
        if not self.client.wait_for_server(timeout_sec=15.0):
            raise RuntimeError("compute_path_to_pose action server unavailable")
        started = time.monotonic()
        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        handle = future.result()
        if not handle.accepted:
            self._write("rejected", started, [], "goal rejected")
            return
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        wrapped = result_future.result()
        result = wrapped.result
        poses = result.path.poses if result else []
        status = "succeeded" if wrapped.status == GoalStatus.STATUS_SUCCEEDED else "failed"
        self._write(status, started, poses, getattr(result, "error_msg", ""))

    def _write(self, status, started, poses, message):
        length = sum(hypot(b.pose.position.x-a.pose.position.x, b.pose.position.y-a.pose.position.y) for a, b in zip(poses, poses[1:]))
        row = {
            "goal_id": str(self.get_parameter("goal_id").value),
            "expected_reachable": bool(self.get_parameter("expected_reachable").value),
            "status": status,
            "planning_time_s": round(time.monotonic() - started, 3),
            "path_length_m": round(length, 3),
            "waypoint_count": len(poses),
            "minimum_clearance_m": None,
            "message": message,
        }
        append_row(str(self.get_parameter("output").value), row)
        self.get_logger().info(str(row))


def main():
    rclpy.init(); node = PlanProbe()
    try: node.run()
    finally: node.destroy_node(); rclpy.shutdown()

