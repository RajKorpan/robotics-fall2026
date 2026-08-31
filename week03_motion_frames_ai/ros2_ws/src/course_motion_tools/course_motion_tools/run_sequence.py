from __future__ import annotations
import json, math, time
from datetime import datetime, timezone
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from .common import SEQUENCES, atomic_json, integrate, output_dir, wrap

def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
class Runner(Node):
    def __init__(self):
        super().__init__("course_motion_sequence")
        self.declare_parameter("sequence_id","straight"); self.sequence_id=str(self.get_parameter("sequence_id").value)
        if self.sequence_id not in SEQUENCES: raise ValueError(f"Unknown sequence: {self.sequence_id}")
        self.segments=SEQUENCES[self.sequence_id]; self.pub=self.create_publisher(Twist,"/student_cmd_vel",10); self.create_subscription(Odometry,"/odom",self.on_odom,10); self.create_timer(0.05,self.tick)
        self.pose=None; self.start=None; self.segment_index=0; self.segment_started=None; self.done=False; self.stop_sent=False
    def on_odom(self,msg): self.pose={"x":msg.pose.pose.position.x,"y":msg.pose.pose.position.y,"theta":yaw(msg.pose.pose.orientation)}
    def tick(self):
        if self.pose is None or self.done: return
        if self.start is None: self.start=dict(self.pose); self.segment_started=time.monotonic()
        if time.monotonic()-self.segment_started>=self.segments[self.segment_index][2]:
            self.pub.publish(Twist()); self.segment_index+=1; self.segment_started=time.monotonic()
            if self.segment_index>=len(self.segments): self.done=True; self.stop_sent=True; return
        v,w,_=self.segments[self.segment_index]; msg=Twist(); msg.linear.x=v; msg.angular.z=w; self.pub.publish(msg)
    def result(self):
        end=self.pose or self.start; dx=end["x"]-self.start["x"]; dy=end["y"]-self.start["y"]; c=math.cos(self.start["theta"]); s=math.sin(self.start["theta"])
        observed={"x":c*dx+s*dy,"y":-s*dx+c*dy,"theta":wrap(end["theta"]-self.start["theta"])}; predicted=integrate(self.segments)
        return {"sequence_id":self.sequence_id,"captured_at":datetime.now(timezone.utc).isoformat(),"segments":[{"linear_x":v,"angular_z":w,"duration":d} for v,w,d in self.segments],"predicted_pose":predicted,"observed_pose":observed,"position_error":math.hypot(observed["x"]-predicted["x"],observed["y"]-predicted["y"]),"heading_error":abs(wrap(observed["theta"]-predicted["theta"])),"completed":self.done,"stop_sent":self.stop_sent}
def append(result):
    path=output_dir()/"motion_sequences.json"; path.parent.mkdir(parents=True,exist_ok=True)
    try: rows=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except json.JSONDecodeError: rows=[]
    rows=[row for row in rows if row.get("sequence_id")!=result["sequence_id"]]; rows.append(result); atomic_json(path,rows); return path
def main(args=None):
    rclpy.init(args=args); node=Runner(); deadline=time.monotonic()+sum(d for _,_,d in node.segments)+10
    try:
        while rclpy.ok() and not node.done and time.monotonic()<deadline: rclpy.spin_once(node,timeout_sec=0.1)
        node.pub.publish(Twist())
        if not node.done: raise RuntimeError("Sequence timed out or no odometry received")
        node.get_logger().info(f"Saved {append(node.result())}")
    finally: node.pub.publish(Twist()); node.destroy_node(); rclpy.shutdown()
if __name__=="__main__": main()

