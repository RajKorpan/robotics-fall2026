from __future__ import annotations
import time,rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from week08_interfaces.msg import TargetObservation
from .behavior_logic import Config,decide
class TargetBehavior(Node):
    def __init__(self):
        super().__init__("target_behavior")
        for name,default in (("min_confidence",.6),("center_deadband",.1),("stop_area",.22),("stale_after",.6),("search_angular",.25),("approach_linear",.1),("center_gain",.7)):self.declare_parameter(name,default)
        self.latest=None;self.received=0.;self.publisher=self.create_publisher(Twist,"/student_cmd_vel",10);self.create_subscription(TargetObservation,"/perception/target",self.on_observation,10);self.create_timer(.1,self.tick)
    def config(self):return Config(**{name:float(self.get_parameter(name).value) for name in Config.__dataclass_fields__})
    def on_observation(self,msg):self.latest={"detected":msg.detected,"confidence":msg.confidence,"center_offset":msg.center_offset,"area_fraction":msg.area_fraction};self.received=time.monotonic()
    def tick(self):
        age=time.monotonic()-self.received if self.latest else float("inf");state,linear,angular=decide(self.latest,age,self.config());command=Twist();command.linear.x=linear;command.angular.z=angular;self.publisher.publish(command);self.get_logger().debug(state)
def main():
    rclpy.init();node=TargetBehavior()
    try:rclpy.spin(node)
    finally:node.publisher.publish(Twist());node.destroy_node();rclpy.shutdown()
