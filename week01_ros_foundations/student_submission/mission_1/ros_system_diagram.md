# Observed ROS 2 system diagram

```mermaid
flowchart LR
  n0["/course_cmd_vel_guard"]
  n1["/course_evidence_collector"]
  n2["/robot_state_publisher"]
  n3["/ros_gz_bridge"]
  n4["/rviz2"]
  n5["/transform_listener_impl_5d1edb9193d0"]
  t0(["/cmd_vel<br/>TwistStamped"])
  n0 -->|publishes| t0
  t0 -->|subscribes| n3
  t1(["/odom<br/>Odometry"])
  n3 -->|publishes| t1
  t1 -->|subscribes| n1
  t2(["/scan<br/>LaserScan"])
  n3 -->|publishes| t2
  t2 -->|subscribes| n1
  t3(["/student_cmd_vel<br/>Twist"])
  t3 -->|subscribes| n0
  t3 -->|subscribes| n1
  t4(["/tf<br/>TFMessage"])
  n2 -->|publishes| t4
  n3 -->|publishes| t4
  t4 -->|subscribes| n5
```

This diagram is generated from the captured publisher and subscriber endpoints. A missing arrow records a missing live endpoint, not an assumed connection.

## Guided terminal observations

| Observation | Completed |
|---|---|
| Listed the running nodes | Yes |
| Inspected the command guard | Yes |
| Inspected the simulator bridge | Yes |
| Inspected the scan connections | Yes |
| Viewed one scan message | Yes |
| Compared proposed and approved command topics | Yes |
