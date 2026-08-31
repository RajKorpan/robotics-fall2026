from __future__ import annotations
import time
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String
from week11_hri_demo.interaction_logic import command_transition


class InteractionDemo(Node):
    def __init__(self):
        super().__init__("week11_interaction_demo")
        defaults = (("motion_enabled", False), ("approach_speed_mps", .08), ("confirmation_required", True), ("timeout_s", 12.0), ("intent_message", "I am approaching to ask how I can help."), ("listening_message", "Listening. Type your request now."))
        for name, default in defaults: self.declare_parameter(name, default)
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.state_pub = self.create_publisher(String, "/hri/state", qos); self.display_pub = self.create_publisher(String, "/hri/display", qos); self.velocity_pub = self.create_publisher(Twist, "/hri/cmd_vel", 10)
        self.create_subscription(String, "/hri/command", self.on_command, 10); self.create_subscription(String, "/hri/text_command", self.on_command, 10); self.create_subscription(Bool, "/hri/emergency_stop", self.on_stop, 10)
        self.state = "IDLE"; self.entered = time.monotonic(); self.pending_after_error = False; self.create_timer(.1, self.tick); self.publish("IDLE", "Ready. Motion is disabled by default.")

    def publish(self, state, display):
        self.state = state; self.entered = time.monotonic(); a, b = String(), String(); a.data, b.data = state, display; self.state_pub.publish(a); self.display_pub.publish(b)
        self.get_logger().info(f"{state}: {display}")

    def stop_motion(self): self.velocity_pub.publish(Twist())

    def tick(self):
        elapsed = time.monotonic() - self.entered
        if self.state == "IDLE" and elapsed >= 1: self.publish("ANNOUNCE", str(self.get_parameter("intent_message").value))
        elif self.state == "ANNOUNCE" and elapsed >= 2: self.publish("APPROACH", "Approaching slowly. Press stop at any time.")
        elif self.state == "APPROACH":
            command = Twist()
            if bool(self.get_parameter("motion_enabled").value): command.linear.x = float(self.get_parameter("approach_speed_mps").value)
            self.velocity_pub.publish(command)
            if elapsed >= 2: self.stop_motion(); self.publish("LISTENING", str(self.get_parameter("listening_message").value))
        elif self.state in ("LISTENING", "CONFIRMING") and elapsed >= float(self.get_parameter("timeout_s").value): self.stop_motion(); self.pending_after_error = True; self.publish("ERROR", "Timed out safely. No action was taken. Send a new request to continue.")
        elif self.state == "ERROR" and self.pending_after_error and elapsed >= 3: self.pending_after_error = False; self.publish("LISTENING", str(self.get_parameter("listening_message").value))
        elif self.state == "ACTING" and elapsed >= 2: self.stop_motion(); self.publish("COMPLETE", "Task simulation complete. What would you like to do next?")

    def on_command(self, msg):
        transition = command_transition(self.state, msg.data, bool(self.get_parameter("confirmation_required").value)); self.pending_after_error = transition.state == "ERROR"; self.publish(transition.state, transition.display)

    def on_stop(self, msg):
        if msg.data: self.stop_motion(); self.pending_after_error = False; self.publish("ERROR", "Emergency stop received. Motion and task execution are stopped.")


def main():
    rclpy.init(); node = InteractionDemo()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.stop_motion(); node.destroy_node(); rclpy.shutdown()
