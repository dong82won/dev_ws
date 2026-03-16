import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    config_dir = os.path.join(get_package_share_directory('custom_teleop_pkg'),
                              'config', 'params.yaml')

    return LaunchDescription([
      Node(
          package='joy',
          executable='joy_node',
          name='joy_node',
          parameters=[{
              'autorepeat_rate': 20.0,
          }]
      ),

      Node(
          package='custom_teleop_pkg',
          executable='custom_teleop_node',
          name='coustom_teleop',
          output='screen',
          parameters=[config_dir]
      ),
    ])
