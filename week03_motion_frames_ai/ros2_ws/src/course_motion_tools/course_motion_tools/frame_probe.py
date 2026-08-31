from __future__ import annotations
import math, time
from datetime import datetime, timezone
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from .common import atomic_json, output_dir

def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
def transform_point(transform,x,y):
    angle=yaw(transform.rotation); c=math.cos(angle); s=math.sin(angle)
    return {"x":transform.translation.x+c*x-s*y,"y":transform.translation.y+s*x+c*y}
def transform_dict(t): return {"translation":{"x":t.translation.x,"y":t.translation.y,"z":t.translation.z},"yaw":yaw(t.rotation)}
class Probe(Node):
    def __init__(self): super().__init__("course_frame_probe"); self.buffer=Buffer(); self.listener=TransformListener(self.buffer,self)
    def capture(self):
        base=self.buffer.lookup_transform("base_link","base_scan",Time()).transform; odom=self.buffer.lookup_transform("odom","base_scan",Time()).transform
        payload={"schema_version":1,"captured_at":datetime.now(timezone.utc).isoformat(),"frames":["odom","base_link","base_scan"],"frame_chain":["odom","base_link","base_scan"],"transforms":{"base_scan_to_base_link":transform_dict(base),"base_scan_to_odom":transform_dict(odom)},"point_prompts":{"sensor_point_in_base":"Transform point (1.0, 0.0) from base_scan to base_link.","sensor_point_in_odom":"Transform point (1.0, 0.0) from base_scan to odom."},"transformed_points":{"sensor_point_in_base":transform_point(base,1.0,0.0),"sensor_point_in_odom":transform_point(odom,1.0,0.0)}}
        path=output_dir()/"frame_snapshot.json"; atomic_json(path,payload); return path
def main(args=None):
    rclpy.init(args=args); node=Probe(); deadline=time.monotonic()+10
    try:
        while rclpy.ok() and time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=0.2)
            try: path=node.capture(); node.get_logger().info(f"Saved {path}"); return
            except Exception: pass
        raise RuntimeError("Required transforms were not available")
    finally: node.destroy_node(); rclpy.shutdown()
if __name__=="__main__": main()

