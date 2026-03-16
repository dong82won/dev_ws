import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node

# this is the function launch  system will look for
def generate_launch_description():

    package_description = "boxbot_description"
    urdf_file = 'box_bot3.urdf'
    robot_desc_path = os.path.join(get_package_share_directory(package_description), "urdf", urdf_file)

    rviz_config_dir = os.path.join(get_package_share_directory(package_description), 'rviz', 'urdf_vis.rviz')
    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz_node',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': True}],
            output='screen'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_node',
        emulate_tty=True,
        parameters=[{'use_sim_time': True, 'robot_description': Command(['xacro ', robot_desc_path])}],
        output="screen"
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',  # [추가 1] 실행 로그를 터미널에서 확인
        # [추가 2] Gazebo가 없으므로 시스템 시간 사용
        parameters=[{'use_sim_time': True }]
    )

    # create and return launch description object
    return LaunchDescription(
        [
            robot_state_publisher_node,
            rviz_node,
            joint_state_publisher_node
        ]
    )