from __future__ import annotations
import math, time
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

class Guard(Node):
    def __init__(self):
        super().__init__("course_cmd_vel_guard")
        self.declare_parameter("max_linear", 0.22); self.declare_parameter("max_angular", 0.8); self.declare_parameter("timeout", 0.5)
        self.max_linear=float(self.get_parameter("max_linear").value); self.max_angular=float(self.get_parameter("max_angular").value); self.timeout=float(self.get_parameter("timeout").value)
        self.pub=self.create_publisher(Twist,"/cmd_vel",10); self.create_subscription(Twist,"/student_cmd_vel",self.on_command,10)
        self.last=0.0; self.moving=False; self.create_timer(0.1,self.watchdog)
    def stop(self): self.pub.publish(Twist()); self.moving=False
    def on_command(self,msg):
        if not all(math.isfinite(float(v)) for v in (msg.linear.x,msg.angular.z)): self.stop(); return
        out=Twist(); out.linear.x=max(-self.max_linear,min(self.max_linear,float(msg.linear.x))); out.angular.z=max(-self.max_angular,min(self.max_angular,float(msg.angular.z)))
        self.pub.publish(out); self.last=time.monotonic(); self.moving=bool(out.linear.x or out.angular.z)
    def watchdog(self):
        if self.moving and time.monotonic()-self.last>self.timeout: self.get_logger().warning("Command timeout; stopping"); self.stop()
def main(args=None):
    rclpy.init(args=args); node=Guard()
    try: rclpy.spin(node)
    finally: node.stop(); node.destroy_node(); rclpy.shutdown()
if __name__=="__main__": main()

