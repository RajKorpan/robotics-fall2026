from __future__ import annotations
import json, time
from pathlib import Path
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Recorder(Node):
    def __init__(self):
        super().__init__("week11_event_recorder")
        for name, default in (("trial_id", "dry_run"), ("design_version", "baseline"), ("output", "runtime/evidence/events.json")): self.declare_parameter(name, default)
        self.started = time.monotonic(); self.events = []
        self.create_subscription(String, "/hri/state", lambda m: self.record("state", m.data), 10); self.create_subscription(String, "/hri/display", lambda m: self.record("display", m.data), 10); self.create_subscription(String, "/hri/command", lambda m: self.record("command", "[primary command received; content omitted]"), 10); self.create_subscription(String, "/hri/text_command", lambda m: self.record("command", "[text command received; content omitted]"), 10)
    def record(self, kind, value): self.events.append({"t_s":round(time.monotonic()-self.started, 3), "kind":kind, "value":value})
    def save(self):
        target = Path(str(self.get_parameter("output").value)); target.parent.mkdir(parents=True, exist_ok=True); payload = {"schema_version":1, "trial_id":str(self.get_parameter("trial_id").value), "design_version":str(self.get_parameter("design_version").value), "events":self.events}; target.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")


def main():
    rclpy.init(); node = Recorder()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.save(); node.destroy_node(); rclpy.shutdown()
