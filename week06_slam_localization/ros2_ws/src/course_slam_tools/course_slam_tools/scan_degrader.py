from __future__ import annotations
import copy, math, random
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

class ScanDegrader(Node):
    def __init__(self):
        super().__init__("scan_degrader"); self.declare_parameter("retention", .50); self.declare_parameter("noise_std", .04); self.rng = random.Random(6006)
        self.publisher = self.create_publisher(LaserScan, "/scan_degraded", qos_profile_sensor_data)
        self.subscription = self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
    def on_scan(self, message):
        if self.rng.random() > float(self.get_parameter("retention").value): return
        output = copy.deepcopy(message); sigma = float(self.get_parameter("noise_std").value)
        output.ranges = [value if not math.isfinite(value) else max(output.range_min, min(output.range_max, value + self.rng.gauss(0, sigma))) for value in output.ranges]
        self.publisher.publish(output)
def main():
    rclpy.init(); node = ScanDegrader()
    try: rclpy.spin(node)
    finally: node.destroy_node(); rclpy.shutdown()
