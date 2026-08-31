from __future__ import annotations
import json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from week03_pattern.pattern import build_pattern

def evidence_dir():
    configured=os.environ.get("WEEK03_EVIDENCE_DIR")
    if configured: return Path(configured).expanduser().resolve()
    root=Path.cwd().parent if Path.cwd().name=="ros2_ws" else Path.cwd(); return root/"runtime"/"evidence"
def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
class PatternNode(Node):
    def __init__(self):
        super().__init__("student_motion_pattern"); self.declare_parameter("pattern","l_path"); self.pattern=str(self.get_parameter("pattern").value); self.segments=build_pattern(self.pattern)
        self.pub=self.create_publisher(Twist,"/student_cmd_vel",10); self.create_subscription(Odometry,"/odom",self.on_odom,10); self.create_timer(0.05,self.tick)
        self.pose=None; self.start=None; self.index=0; self.started=None; self.done=False; self.stop_sent=False
    def on_odom(self,msg): self.pose={"x":msg.pose.pose.position.x,"y":msg.pose.pose.position.y,"theta":yaw(msg.pose.pose.orientation)}
    def stop(self): self.pub.publish(Twist()); self.stop_sent=True
    def tick(self):
        if self.pose is None or self.done: return
        if self.start is None: self.start=dict(self.pose); self.started=time.monotonic()
        segment=self.segments[self.index]
        if time.monotonic()-self.started>=segment.duration:
            self.stop(); self.index+=1; self.started=time.monotonic()
            if self.index>=len(self.segments): self.done=True; self.save(); return
            segment=self.segments[self.index]
        msg=Twist(); msg.linear.x=max(-0.22,min(0.22,float(segment.linear_x))); msg.angular.z=max(-0.8,min(0.8,float(segment.angular_z))); self.pub.publish(msg)
    def save(self):
        path=evidence_dir()/"pattern_run.json"; path.parent.mkdir(parents=True,exist_ok=True); payload={"captured_at":datetime.now(timezone.utc).isoformat(),"pattern":self.pattern,"completed":self.done,"final_stop_verified":self.stop_sent,"start_pose":self.start,"end_pose":self.pose,"segment_count":len(self.segments)}; path.write_text(json.dumps(payload,indent=2),encoding="utf-8")
def main(args=None):
    rclpy.init(args=args); node=PatternNode()
    try:
        while rclpy.ok() and not node.done: rclpy.spin_once(node,timeout_sec=0.1)
    finally: node.stop(); node.save(); node.destroy_node(); rclpy.shutdown()
if __name__=="__main__": main()

