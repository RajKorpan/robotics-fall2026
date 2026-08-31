from __future__ import annotations
from pathlib import Path
import time
import cv2, numpy as np, rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from week08_interfaces.msg import TargetObservation
class LearnedDetector(Node):
    def __init__(self):
        super().__init__("learned_detector")
        for name,default in (("camera_topic","/camera/image_raw"),("model_path",""),("labels_path",""),("target_label","bottle"),("confidence_threshold",.5),("nms_threshold",.45),("input_size",640)):self.declare_parameter(name,default)
        model=Path(str(self.get_parameter("model_path").value)); labels=Path(str(self.get_parameter("labels_path").value))
        if not model.exists() or not labels.exists():raise FileNotFoundError("Instructor-provided detector.onnx and labels.txt are required")
        self.net=cv2.dnn.readNetFromONNX(str(model)); self.labels=[line.strip() for line in labels.read_text(encoding="utf-8").splitlines() if line.strip()]; self.bridge=CvBridge(); self.obs=self.create_publisher(TargetObservation,"/perception/target",10); self.annotated=self.create_publisher(Image,"/perception/annotated",10); self.create_subscription(Image,str(self.get_parameter("camera_topic").value),self.on_image,qos_profile_sensor_data)
    def detections(self,image):
        size=int(self.get_parameter("input_size").value); blob=cv2.dnn.blobFromImage(image,1/255.,(size,size),swapRB=True,crop=False); self.net.setInput(blob); output=np.squeeze(self.net.forward())
        if output.ndim!=2:return []
        if output.shape[0]<output.shape[1]:output=output.T
        boxes=[];scores=[];ids=[]; sx=image.shape[1]/size; sy=image.shape[0]/size; threshold=float(self.get_parameter("confidence_threshold").value)
        for row in output:
            if len(row)<5:continue
            class_scores=row[4:]; class_id=int(np.argmax(class_scores)); confidence=float(class_scores[class_id])
            if confidence<threshold or class_id>=len(self.labels):continue
            cx,cy,w,h=map(float,row[:4]); boxes.append([int((cx-w/2)*sx),int((cy-h/2)*sy),int(w*sx),int(h*sy)]);scores.append(confidence);ids.append(class_id)
        keep=cv2.dnn.NMSBoxes(boxes,scores,threshold,float(self.get_parameter("nms_threshold").value)); indices=np.array(keep).reshape(-1).tolist() if len(keep) else []
        return [(boxes[i],scores[i],self.labels[ids[i]]) for i in indices]
    def on_image(self,msg):
        started=time.perf_counter(); image=self.bridge.imgmsg_to_cv2(msg,"bgr8"); detections=self.detections(image); target=str(self.get_parameter("target_label").value); matches=[item for item in detections if item[2]==target]; out=TargetObservation(); out.header=msg.header; out.label=target; annotated=image.copy()
        for (x,y,w,h),score,label in detections:cv2.rectangle(annotated,(x,y),(x+w,y+h),(255,100,0),2);cv2.putText(annotated,f"{label} {score:.2f}",(x,max(15,y-5)),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,100,0),1)
        if matches:
            (x,y,w,h),score,_=max(matches,key=lambda item:item[1]); out.detected=True;out.confidence=float(score);out.center_offset=float(((x+w/2)/(image.shape[1]/2))-1);out.area_fraction=float((w*h)/(image.shape[0]*image.shape[1]));out.bbox_x=max(0,x);out.bbox_y=max(0,y);out.bbox_width=max(0,w);out.bbox_height=max(0,h)
        out.latency_ms=float((time.perf_counter()-started)*1000); self.obs.publish(out); ann=self.bridge.cv2_to_imgmsg(annotated,"bgr8");ann.header=msg.header;self.annotated.publish(ann)
def main():
    rclpy.init();node=LearnedDetector()
    try:rclpy.spin(node)
    finally:node.destroy_node();rclpy.shutdown()
