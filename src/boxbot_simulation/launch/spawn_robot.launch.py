import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    # 1. 패키지 경로 및 설정
    pkg_description = get_package_share_directory('boxbot_description')

    # 2. 런치 인자 정의 (Spawn 위치 및 시뮬레이션 시간)
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='0.0', description='Spawn X position')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='0.0', description='Spawn Y position')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.2', description='Spawn Z position')
    # 모든 노드에 시뮬레이션 시간을 사용하도록 인자 추가
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation clock')

    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # 3. URDF 파일 읽기
    urdf_file_path = os.path.join(pkg_description, 'urdf', 'box_bot3.urdf')
    with open(urdf_file_path, 'r') as infp:
        robot_desc = infp.read()

    # 4. Robot State Publisher 노드 (TF 트리 구성)
    # publish_frequency를 50Hz로 높여 고정 좌표(Fixed Joint)의 시간 멈춤을 방지합니다.
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_node',
        emulate_tty=True,
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc,
            #'ignore_timestamp': False,
            #'publish_frequency': 50.0, # TF 발행 주기를 강제하여 0.0초 방지
            #'use_tf_static': False
        }],
        output="screen"
    )

    # # 5. Joint State Publisher 노드 (추가됨)
    # # 가제보의 joint_states를 받아 robot_state_publisher가 시간을 올바르게 계산하도록 돕습니다.
    # joint_state_publisher_node = Node(
    #     package='joint_state_publisher',
    #     executable='joint_state_publisher',
    #     name='joint_state_publisher',
    #     parameters=[{'use_sim_time': use_sim_time}],
    #     output='screen'
    # )

    # 6. Gazebo 로봇 Spawn 노드
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'box_bot',
            '-topic', 'robot_description',
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose,
            '-timeout', '60.0'
        ],
        output='screen'
    )

    # 7. 실행 리스트 반환
    return LaunchDescription([
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        use_sim_time_arg,
        robot_state_publisher_node,
        # joint_state_publisher_node, # 추가된 노드
        spawn_entity_node
    ])