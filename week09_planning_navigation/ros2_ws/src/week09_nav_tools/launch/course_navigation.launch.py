from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    map_file = LaunchConfiguration("map")
    gazebo = IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare("turtlebot3_gazebo"), "launch", "turtlebot3_world.launch.py"])))
    navigation = IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare("turtlebot3_navigation2"), "launch", "navigation2.launch.py"])), launch_arguments={"map": map_file, "use_sim_time": "true"}.items())
    return LaunchDescription([DeclareLaunchArgument("map", description="Absolute path to the Week 6 map YAML"), gazebo, navigation])

