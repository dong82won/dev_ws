import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    ld = LaunchDescription()

    config_dir = os.path.join(get_package_share_directory('custom_teleop_pkg'),
                            'config', 'params.yaml')

    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value= config_dir,
        description='Path to the config file to use'
    )
    ld.add_action(params_file_arg)

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'autorepeat_rate': 20.0,
        }]
    )
    ld.add_action(joy_node)

    custom_teleop_node= Node(
        package='custom_teleop_pkg',
        executable='custom_teleop_node',
        name='coustom_teleop',
        output='screen',
        parameters=[LaunchConfiguration('params_file')]
    )
    ld.add_action(custom_teleop_node)

    return ld
