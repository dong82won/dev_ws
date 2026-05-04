import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, FindExecutable
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.descriptions import ParameterValue


def generate_launch_description():

    # 1. 인자 선언
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='0.0')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='0.0')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.2')
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true')

    # 2. 파라미터 참조
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    use_sim_time = LaunchConfiguration('use_sim_time')


    #pkg_description = get_package_share_directory('turtlebot3_description')
    pkg_description = get_package_share_directory('tb3_description')

    # 3. XACRO 명령 실행 (ROS 2 표준 방식)
    xacro_file_path = os.path.join(pkg_description, 'urdf', 'tb3_burger_main.urdf.xacro')
    robot_desc = ParameterValue( Command([FindExecutable(name='xacro'),' ', xacro_file_path]), value_type=str)

    # # 4. URDF 파일 직접 읽기
    # urdf_file_path = os.path.join(pkg_description, 'urdf', 'tb3_burger_gazebo_new.urdf')
    # with open(urdf_file_path, 'r') as infp:
    #     robot_desc = infp.read()

    # 4. Robot State Publisher 노드 설정
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
                    'use_sim_time': use_sim_time,
                    'robot_description': robot_desc,
                    }],
        output="screen"
    )
    # 5. Gazebo에 로봇 소환 (Spawn Entity)
    spawn_entity_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'my_robot',
            '-topic', 'robot_description',
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose
        ],
        output='screen'
    )

    # 6. ros2_control 제어기 스폰 (Spawner) 조인트 상태를 발행하는 노드
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # 차동 구동 제어기 (가속도 제한이 적용된 실제 드라이버)
    diff_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # # 7. 실행 순서 보장 (로봇 소환 후 제어기 실행)
    # # 로봇이 가제보에 완전히 나타난 뒤 제어기를 로드하도록 이벤트 핸들러 설정
    # load_joint_state_broadcaster = RegisterEventHandler(
    #     event_handler=OnProcessExit(
    #         target_action=spawn_entity_node,
    #         on_exit=[joint_state_broadcaster_spawner],
    #     )
    # )

    # load_diff_drive_controller = RegisterEventHandler(
    #     event_handler=OnProcessExit(
    #         target_action=joint_state_broadcaster_spawner,
    #         on_exit=[diff_drive_controller_spawner],
    #     )
    # )

    # 7. 실행 순서 최적화 (병렬 실행)
    # 로봇 소환(spawn_entity_node)이 완료되면 두 제어기를 동시에 실행합니다.
    load_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity_node,
            on_exit=[
                joint_state_broadcaster_spawner,
                diff_drive_controller_spawner
            ],
        )
    )


    return LaunchDescription([
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        use_sim_time_arg,
        robot_state_publisher_node,
        spawn_entity_node,
        # 이벤트 핸들러를 통해 순차적 실행 보장
        #load_joint_state_broadcaster,
        #load_diff_drive_controller
        load_controllers
    ])
