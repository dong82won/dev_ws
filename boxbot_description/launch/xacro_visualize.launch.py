import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # 패키지 이름 설정 (사용자의 패키지명에 맞게 수정하세요)
    package_name = 'my_box_bot_description'
    pkg_description = get_package_share_directory(package_name)

    # 1. Xacro 파일 경로 설정
    xacro_file = os.path.join(pkg_description, 'urdf', 'box_bot3.urdf.xacro')
    # 2. 로봇 모델 처리 (Xacro -> URDF 문자열 변환) 
    robot_description_content = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # RViz 설정 파일 경로 [cite: 10]
    default_rviz_config_path = PathJoinSubstitution([pkg_description, 'rviz', 'urdf_vis.rviz'])

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config_path,
        description='Absolute path to rviz config file'
    )

    # 3. 로봇 상태 발행 노드 [cite: 11, 12]
    # URDF 데이터를 /robot_description 토픽으로 발행합니다.
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': False  # Gazebo가 없으므로 시스템 시간을 사용합니다.
        }]
    )

    # 4. 조인트 상태 발행 노드 (GUI 포함)
    # Gazebo 플러그인이 없으므로, GUI를 통해 수동으로 조인트를 움직여볼 수 있습니다.
    joint_state_publisher_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
    )

    # 5. RViz2 실행 노드 [cite: 10]
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        output='screen'
    )

    return LaunchDescription([
        rviz_config_arg,
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node
    ])