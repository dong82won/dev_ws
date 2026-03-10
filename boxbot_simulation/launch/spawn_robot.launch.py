import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    # 패키지 경로
    pkg_description = get_package_share_directory('boxbot_description')

    # URDF 파일 경로
    urdf_file = os.path.join(pkg_description, 'urdf', 'box_bot3.urdf')
    xacro_file = os.path.join(pkg_description, 'urdf', 'box_bot3.urdf.xacro')

    # 파라미터 참조 (상위 런치 파일에서 정의됨)
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='0.0', description='Spawn X position')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='0.0', description='Spawn Y position')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.2', description='Spawn Z position')

    # Spawn 위치 파라미터
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')

    # URDF 내용을 읽어오기 위한 Command 객체
    robot_desc = ParameterValue(Command(['xacro ', urdf_file]),value_type=str)
    #robot_desc = ParameterValue(Command(['xacro ', xacro_file]),value_type=str)

    # robot_state_publisher 노드
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_node',
        emulate_tty=True,
        parameters=[{'use_sim_time': True,
                    'robot_description': robot_desc
                    }],
        output="screen"
    )

    # 로봇 모델 spawn 노드
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'box_bot',
            '-topic', 'robot_description',
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose,
            '-timeout', '120.0'  # [추가] 대기 시간을 120초로 연장
        ],
        output='screen'
    )

    return LaunchDescription([
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        robot_state_publisher_node,
        spawn_entity_node
    ])