from __future__ import annotations
import json, math, time
from pathlib import Path
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

class Recorder(Node):
    def __init__(self):
        super().__init__("localization_recorder")
        for name, default in (("condition", "good_initial_pose"), ("duration", 30.0), ("output", "localization.json")): self.declare_parameter(name, default)
        self.started = time.monotonic(); self.samples = []; self.raw_scans = 0; self.used_scans = 0
        self.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self.on_pose, 10)
        self.create_subscription(LaserScan, "/scan", lambda _: setattr(self, "raw_scans", self.raw_scans + 1), qos_profile_sensor_data)
        self.create_subscription(LaserScan, "/scan_degraded", lambda _: setattr(self, "used_scans", self.used_scans + 1), qos_profile_sensor_data)
        self.create_timer(.25, self.tick)
    def on_pose(self, msg):
        q = msg.pose.pose.orientation; yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)); covariance = msg.pose.covariance
        self.samples.append({"time": time.monotonic() - self.started, "x": msg.pose.pose.position.x, "y": msg.pose.pose.position.y, "yaw": yaw, "covariance_trace": covariance[0] + covariance[7] + covariance[35]})
    def tick(self):
        if time.monotonic() - self.started < float(self.get_parameter("duration").value): return
        condition = str(self.get_parameter("condition").value); valid = self.samples; settled = valid[max(0, len(valid) - 20):]
        if valid:
            cx = sum(row["x"] for row in settled) / len(settled); cy = sum(row["y"] for row in settled) / len(settled)
            spread = math.sqrt(sum((row["x"] - cx) ** 2 + (row["y"] - cy) ** 2 for row in settled) / len(settled)); jumps = [math.hypot(b["x"] - a["x"], b["y"] - a["y"]) for a, b in zip(valid, valid[1:])]
            convergence = next((row["time"] for row in valid if row["covariance_trace"] <= .5), None)
            metrics = {"sample_count": len(valid), "duration": valid[-1]["time"] - valid[0]["time"], "convergence_time": convergence, "final_covariance": valid[-1]["covariance_trace"], "settled_position_spread": spread, "pose_jump": max(jumps, default=0.0)}
        else: metrics = {"sample_count": 0, "duration": 0, "convergence_time": None, "final_covariance": None, "settled_position_spread": None, "pose_jump": None}
        metrics["scan_retention"] = self.used_scans / max(1, self.raw_scans) if condition == "degraded_sensor" else 1.0
        payload = {"schema_version": 1, "condition": condition, "metrics": metrics, "samples": valid}
        path = Path(str(self.get_parameter("output").value)); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.get_logger().info(f"Saved {path}"); rclpy.shutdown()
def main():
    rclpy.init(); node = Recorder()
    try: rclpy.spin(node)
    finally: node.destroy_node()
