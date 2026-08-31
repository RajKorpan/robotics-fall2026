from __future__ import annotations

import json
from math import hypot
from pathlib import Path
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


class SocialMonitor(Node):
    def __init__(self):
        super().__init__("week09_social_monitor")
        for name, default in (("scenario_file", "assets/scenarios/people.json"), ("output", "runtime/evidence/social_run.json"), ("run_label", "baseline"), ("goal_id", "social_goal")):
            self.declare_parameter(name, default)
        scenario = json.loads(Path(str(self.get_parameter("scenario_file").value)).read_text(encoding="utf-8"))
        self.people = scenario["people"]; self.document = {"schema_version": 1, "run_label": str(self.get_parameter("run_label").value), "scenario_id": scenario["scenario_id"], "goal_id": str(self.get_parameter("goal_id").value), "required_clearance_m": scenario["required_clearance_m"], "monitor_radius_m": scenario["monitor_radius_m"], "sample_period_s": 0.1, "samples": []}
        self.speed = 0.0; self.last_sample = 0.0
        self.create_subscription(Twist, "/cmd_vel", self.on_twist, 20); self.create_subscription(Odometry, "/odom", self.on_odom, 20)

    def on_twist(self, msg): self.speed = hypot(msg.linear.x, msg.linear.y)

    def on_odom(self, msg):
        now = time.monotonic()
        if now - self.last_sample < self.document["sample_period_s"]: return
        x, y = msg.pose.pose.position.x, msg.pose.pose.position.y
        nearest = min(hypot(x-p["x"], y-p["y"])-p.get("radius_m", 0) for p in self.people)
        self.document["samples"].append({"t_s": round(now, 3), "x": round(x, 3), "y": round(y, 3), "speed_mps": round(self.speed, 3), "nearest_person_m": round(nearest, 3)})
        self.last_sample = now

    def save(self):
        target = Path(str(self.get_parameter("output").value)); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(self.document, indent=2)+"\n", encoding="utf-8")


def main():
    rclpy.init(); node = SocialMonitor()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.save(); node.destroy_node(); rclpy.shutdown()

