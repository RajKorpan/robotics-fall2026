from __future__ import annotations
import csv,time
from pathlib import Path
import rclpy
from rclpy.node import Node
from week08_interfaces.msg import TargetObservation
class Recorder(Node):
    def __init__(self):
        super().__init__("observation_recorder")
        for name,default in (("condition","normal"),("expected",True),("duration",5.),("output","runtime/evidence/perception.csv")):self.declare_parameter(name,default)
        self.started=time.monotonic();self.count=0;self.detected=0;self.confidences=[];self.latencies=[];self.create_subscription(TargetObservation,"/perception/target",self.on_obs,10);self.create_timer(.2,self.tick)
    def on_obs(self,msg):self.count+=1;self.detected+=int(msg.detected);self.confidences.append(float(msg.confidence));self.latencies.append(float(msg.latency_ms))
    def tick(self):
        if time.monotonic()-self.started<float(self.get_parameter("duration").value):return
        path=Path(str(self.get_parameter("output").value));path.parent.mkdir(parents=True,exist_ok=True);exists=path.exists();row={"condition":str(self.get_parameter("condition").value),"expected":bool(self.get_parameter("expected").value),"detected":self.detected>=max(1,self.count*.3),"confidence":sum(self.confidences)/max(1,len(self.confidences)),"latency_ms":sum(self.latencies)/max(1,len(self.latencies)),"frame_count":self.count}
        with path.open("a",newline="",encoding="utf-8") as handle:writer=csv.DictWriter(handle,fieldnames=row);writer.writeheader() if not exists else None;writer.writerow(row)
        self.get_logger().info(f"Recorded {row}");rclpy.shutdown()
def main():
    rclpy.init();node=Recorder()
    try:rclpy.spin(node)
    finally:node.destroy_node()
