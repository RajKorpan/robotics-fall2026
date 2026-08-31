from __future__ import annotations
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
def generate_launch_description():
    gazebo=os.path.join(get_package_share_directory("turtlebot3_gazebo"),"launch","empty_world.launch.py")
    return LaunchDescription([SetEnvironmentVariable("TURTLEBOT3_MODEL","burger"),IncludeLaunchDescription(PythonLaunchDescriptionSource(gazebo)),Node(package="course_cmd_vel_guard",executable="cmd_vel_guard",output="screen"),Node(package="rviz2",executable="rviz2",name="rviz2",output="screen")])

