from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, SetRemap
from launch_ros.substitutions import FindPackageShare
def generate_launch_description():
    map_file = LaunchConfiguration("map"); degraded = LaunchConfiguration("degraded")
    gazebo = IncludeLaunchDescription(PythonLaunchDescriptionSource([FindPackageShare("turtlebot3_gazebo"), "/launch/turtlebot3_world.launch.py"]))
    def navigation(): return IncludeLaunchDescription(PythonLaunchDescriptionSource([FindPackageShare("turtlebot3_navigation2"), "/launch/navigation2.launch.py"]), launch_arguments={"map": map_file, "use_sim_time": "true"}.items())
    degraded_group = GroupAction(condition=IfCondition(PythonExpression(["'", degraded, "' == 'degraded'"])), actions=[SetRemap(src="/scan", dst="/scan_degraded"), navigation()])
    normal_group = GroupAction(condition=IfCondition(PythonExpression(["'", degraded, "' != 'degraded'"])), actions=[navigation()])
    degrader = Node(package="course_slam_tools", executable="scan_degrader", condition=IfCondition(PythonExpression(["'", degraded, "' == 'degraded'"])), parameters=[{"use_sim_time": True, "retention": .5, "noise_std": .04}])
    return LaunchDescription([DeclareLaunchArgument("map"), DeclareLaunchArgument("degraded", default_value="normal"), gazebo, degrader, degraded_group, normal_group])
