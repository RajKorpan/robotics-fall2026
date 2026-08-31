from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration,PythonExpression
from launch_ros.actions import Node
def generate_launch_description():
    mode=LaunchConfiguration("mode");camera=LaunchConfiguration("camera_topic");model=LaunchConfiguration("model_path");labels=LaunchConfiguration("labels_path");enabled=LaunchConfiguration("enable_behavior")
    classical=Node(package="week08_perception",executable="classical_detector",condition=IfCondition(PythonExpression(["'",mode,"' == 'classical'"])),parameters=[{"camera_topic":camera}]);learned=Node(package="week08_perception",executable="learned_detector",condition=IfCondition(PythonExpression(["'",mode,"' == 'learned'"])),parameters=[{"camera_topic":camera,"model_path":model,"labels_path":labels}]);behavior=Node(package="week08_perception",executable="target_behavior",condition=IfCondition(enabled));guard=Node(package="course_cmd_vel_guard",executable="guard")
    return LaunchDescription([DeclareLaunchArgument("mode",default_value="classical"),DeclareLaunchArgument("camera_topic",default_value="/camera/image_raw"),DeclareLaunchArgument("enable_behavior",default_value="false"),DeclareLaunchArgument("model_path",default_value=""),DeclareLaunchArgument("labels_path",default_value=""),classical,learned,behavior,guard])
