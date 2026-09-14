# Mission 1

## Command Path Explanation

A proposed command travels on student_cmd_vel, this part drives the command that comes from a student's program before they are checked to see if it is safe. While the guard subscribes it /cmd_vel and decides if the proposed command is safe to execute, then if deemed safe the guard publishes the command to _vel. There is a whole process that must happen to ensure safety. 

## Graph Explanation

A ROS 2 graph is a live map of running nodes that work to communicate with other parts within the system of the robot. Nodes work with topics. An exmaple of a node is /rviz2 and a topic is /scan. 

## Guided Checks

{'bridge_info': True, 'command_topics': True, 'guard_info': True, 'node_list': True, 'scan_info': True, 'scan_message': True}

## Scan Observation

I found various ranges and values, the highest being 3.5. Which represents the maximum distance the LiDAR can measure, so there is no obstacle detected within that distance. 

## Tools Explanation

Gazebo is responsible to simulating the environment that a robot is in as well as the physics of the robot in general. This is where  motion is calculated, possible collision, and what the senors would detect in its environment. While Rviz is responsible for actually visualizing the data so a person can see it, like LiDAR readings. 
