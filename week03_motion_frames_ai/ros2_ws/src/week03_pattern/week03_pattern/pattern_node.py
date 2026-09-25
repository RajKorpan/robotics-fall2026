"""Course-provided bounded ROS wrapper for the student's segment list."""
import json
import math
import os
from pathlib import Path
import signal
import time
from datetime import datetime, timezone
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from week03_pattern.pattern import build_pattern
from week03_pattern.checks import validate, endpoint, source_hash


def main(args=None):
    rclpy.init(args=args)
    node=Node('student_motion_pattern');node.declare_parameter('pattern','l_path')
    name=str(node.get_parameter('pattern').value)
    pub=node.create_publisher(Twist,'/student_cmd_vel',10)
    readings=[];checkpoints=[];completed=False;interrupted=False;error='';start=None;stopped=False
    root=Path(os.environ.get('WEEK03_SOURCE_ROOT',Path(__file__).resolve().parents[1]))
    signature=source_hash(root)
    def receive(msg):
        p,q=msg.pose.pose.position,msg.pose.pose.orientation
        readings.append((time.monotonic(),{'x':p.x,'y':p.y,'theta':math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))},
                         abs(msg.twist.twist.linear.x),abs(msg.twist.twist.angular.z)))
    node.create_subscription(Odometry,'/odom',receive,qos_profile_sensor_data)
    def pump(duration,v=0.,w=0.,monitor=False):
        deadline=time.monotonic()+duration
        while time.monotonic()<deadline and rclpy.ok():
            if monitor and (not readings or time.monotonic()-readings[-1][0]>.5):
                raise RuntimeError('Odometry became stale; stopping')
            msg=Twist();msg.linear.x=float(v);msg.angular.z=float(w);pub.publish(msg)
            rclpy.spin_once(node,timeout_sec=.02);time.sleep(.02)
    def interrupt(*_): raise KeyboardInterrupt
    signal.signal(signal.SIGINT,interrupt);signal.signal(signal.SIGTERM,interrupt)
    def relative(p):
        dx,dy=p['x']-start['x'],p['y']-start['y'];a=p['theta']-start['theta']
        return {'x':math.cos(start['theta'])*dx+math.sin(start['theta'])*dy,
                'y':-math.sin(start['theta'])*dx+math.cos(start['theta'])*dy,
                'theta':math.atan2(math.sin(a),math.cos(a))}
    try:
        segments=build_pattern(name);validate(segments)
        wait=time.monotonic()+10
        while time.monotonic()<wait and (not readings or pub.get_subscription_count()==0): pump(.1)
        if not readings or pub.get_subscription_count()==0: raise RuntimeError('Start Gazebo and the course command guard first')
        pump(.5);start=dict(readings[-1][1])
        node.get_logger().info('Starting assigned pattern; Ctrl+C tests interruption cleanup')
        for i,s in enumerate(segments):
            pump(s.duration,s.linear_x,s.angular_z,monitor=True)
            pump(.25,monitor=True)
            actual=relative(readings[-1][1]);expected=endpoint(segments[:i+1]);angle=actual['theta']-expected['theta']
            checkpoints.append({'expected':expected,'observed':actual,
                'position_error':math.hypot(actual['x']-expected['x'],actual['y']-expected['y']),
                'heading_error':abs(math.atan2(math.sin(angle),math.cos(angle)))})
        completed=True
    except KeyboardInterrupt:
        interrupted=True;error='Interrupted by user or process timeout'
    except Exception as exc:
        error=f'{type(exc).__name__}: {exc}'
    finally:
        if rclpy.ok():
            # Stopping is the wrapper's responsibility, even if validation or
            # timing calculations fail. Never derive the final command from a segment.
            stop_time=time.monotonic();pump(.6,0.,0.)
            stopped=bool(readings and readings[-1][0]>=stop_time and readings[-1][2]<.02 and readings[-1][3]<.05)
        directory=Path(os.environ.get('WEEK03_EVIDENCE_DIR','runtime/evidence'));directory.mkdir(parents=True,exist_ok=True)
        payload={'captured_at':datetime.now(timezone.utc).isoformat(),'pattern':name,'source_sha256':signature,
                 'attempt_id':os.environ.get('WEEK03_ATTEMPT_ID',''),
                 'completed':completed,'interrupted':interrupted,'error':error,'final_stop_verified':stopped,
                 'shape_observed':bool(completed and checkpoints and all(c['position_error']<=.15 and c['heading_error']<=.20 for c in checkpoints)),
                 'start_pose':start,'end_pose':readings[-1][1] if readings else None,'checkpoints':checkpoints}
        target=directory/('pattern_interrupt.json' if interrupted else 'pattern_run.json')
        temp=target.with_suffix('.tmp');temp.write_text(json.dumps(payload,indent=2),encoding='utf-8');temp.replace(target)
        if rclpy.ok(): node.destroy_node();rclpy.shutdown()
        print(json.dumps(payload,indent=2))
    if error or not completed or not stopped: raise SystemExit(1)


if __name__=='__main__': main()
