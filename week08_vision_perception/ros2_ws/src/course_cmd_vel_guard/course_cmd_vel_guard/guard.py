import math, time
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
class Guard(Node):
    def __init__(self):
        super().__init__("course_cmd_vel_guard"); self.declare_parameter("max_linear",.12); self.declare_parameter("max_angular",.6); self.declare_parameter("timeout",.5); self.last=0.; self.stopped=True
        self.out=self.create_publisher(Twist,"/cmd_vel",10); self.create_subscription(Twist,"/student_cmd_vel",self.on_command,10); self.create_timer(.1,self.watchdog)
    def stop(self): self.out.publish(Twist()); self.stopped=True
    def on_command(self,msg):
        if not all(math.isfinite(v) for v in (msg.linear.x,msg.angular.z)): self.stop(); return
        guarded=Twist(); guarded.linear.x=max(-float(self.get_parameter("max_linear").value),min(float(self.get_parameter("max_linear").value),msg.linear.x)); guarded.angular.z=max(-float(self.get_parameter("max_angular").value),min(float(self.get_parameter("max_angular").value),msg.angular.z)); self.out.publish(guarded); self.last=time.monotonic(); self.stopped=guarded.linear.x==0 and guarded.angular.z==0
    def watchdog(self):
        if not self.stopped and time.monotonic()-self.last>float(self.get_parameter("timeout").value): self.stop()
def main():
    rclpy.init(); node=Guard()
    try: rclpy.spin(node)
    finally: node.stop(); node.destroy_node(); rclpy.shutdown()
