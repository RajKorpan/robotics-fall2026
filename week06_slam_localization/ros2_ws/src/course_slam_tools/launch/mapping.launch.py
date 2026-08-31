from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from pathlib import Path
def generate_launch_description():
    gazebo = IncludeLaunchDescription(PythonLaunchDescriptionSource([FindPackageShare("turtlebot3_gazebo"), "/launch/turtlebot3_world.launch.py"]))
    slam = IncludeLaunchDescription(PythonLaunchDescriptionSource([FindPackageShare("slam_toolbox"), "/launch/online_async_launch.py"]), launch_arguments={"use_sim_time": "true"}.items())
    return LaunchDescription([gazebo, slam])
