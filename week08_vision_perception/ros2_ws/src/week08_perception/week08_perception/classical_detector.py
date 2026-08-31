from __future__ import annotations
import time, cv2, numpy as np, rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from week08_interfaces.msg import TargetObservation
class ClassicalDetector(Node):
    def __init__(self):
        super().__init__("classical_detector"); defaults=(("h_low",40),("s_low",70),("v_low",40),("h_high",90),("s_high",255),("v_high",255),("min_area",300.0),("kernel",5))
        for name,value in defaults:self.declare_parameter(name,value)
        self.declare_parameter("camera_topic","/camera/image_raw"); self.bridge=CvBridge(); self.obs=self.create_publisher(TargetObservation,"/perception/target",10); self.mask=self.create_publisher(Image,"/perception/mask",10); self.annotated=self.create_publisher(Image,"/perception/annotated",10); self.create_subscription(Image,str(self.get_parameter("camera_topic").value),self.on_image,qos_profile_sensor_data)
    def on_image(self,msg):
        started=time.perf_counter(); image=self.bridge.imgmsg_to_cv2(msg,"bgr8"); hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV); lower=np.array([self.get_parameter(x).value for x in ("h_low","s_low","v_low")]); upper=np.array([self.get_parameter(x).value for x in ("h_high","s_high","v_high")]); mask=cv2.inRange(hsv,lower,upper); k=max(1,int(self.get_parameter("kernel").value)); kernel=np.ones((k,k),np.uint8); mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel); mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel); contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); contour=max(contours,key=cv2.contourArea) if contours else None; out=TargetObservation(); out.header=msg.header; out.label="course_target"; annotated=image.copy(); minimum=float(self.get_parameter("min_area").value)
        if contour is not None and cv2.contourArea(contour)>=minimum:
            x,y,w,h=cv2.boundingRect(contour); area=cv2.contourArea(contour); out.detected=True; out.confidence=float(min(1.,area/max(minimum*4,1))); out.center_offset=float(((x+w/2)/(image.shape[1]/2))-1); out.area_fraction=float(area/(image.shape[0]*image.shape[1])); out.bbox_x=x; out.bbox_y=y; out.bbox_width=w; out.bbox_height=h; cv2.rectangle(annotated,(x,y),(x+w,y+h),(0,255,0),2)
        out.latency_ms=float((time.perf_counter()-started)*1000); self.obs.publish(out); mask_msg=self.bridge.cv2_to_imgmsg(mask,"mono8"); mask_msg.header=msg.header; self.mask.publish(mask_msg); ann_msg=self.bridge.cv2_to_imgmsg(annotated,"bgr8"); ann_msg.header=msg.header; self.annotated.publish(ann_msg)
def main():
    rclpy.init(); node=ClassicalDetector()
    try:rclpy.spin(node)
    finally:node.destroy_node();rclpy.shutdown()
