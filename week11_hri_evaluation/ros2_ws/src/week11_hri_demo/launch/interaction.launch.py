from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    motion = LaunchConfiguration("motion_enabled"); config = LaunchConfiguration("config")
    baseline = PathJoinSubstitution([FindPackageShare("week11_hri_demo"), "config", "baseline.yaml"])
    return LaunchDescription([DeclareLaunchArgument("motion_enabled", default_value="false"), DeclareLaunchArgument("config", default_value=baseline), Node(package="week11_hri_demo", executable="interaction_demo", parameters=[config, {"motion_enabled":motion}])])

