import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, FindExecutable
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch_ros.descriptions import ParameterValue

def generate_launch_description():

    # [개선] 메인 런치에서 전달받은 UDP 설정 경로
    udp_config_uri_arg = DeclareLaunchArgument('udp_config_uri', default_value='')
    udp_config_uri = LaunchConfiguration('udp_config_uri')

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
    robot_desc = ParameterValue( Command([FindExecutable(name='xacro'), ' ', xacro_file_path]), value_type=str)

    # # 4. URDF 파일 직접 읽기
    # urdf_file_path = os.path.join(pkg_description, 'urdf', 'tb3_burger_gazebo_new.urdf')
    # with open(urdf_file_path, 'r') as infp:
    #     robot_desc = infp.read()

    # 4. 노드 설정
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
                    'use_sim_time': use_sim_time,
                    'robot_description': robot_desc,
                    }],
        output="screen"
    )
    # [수정] GroupAction으로 로봇 스테이트 퍼블리셔에만 UDP 적용
    robot_state_publisher_group = GroupAction([
        SetEnvironmentVariable('CYCLONEDDS_URI', udp_config_uri),
        robot_state_publisher_node
    ])

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
        # spawn_entity는 가제보와 대화해야 하므로 기본 SHM 설정을 따르도록 둠
        output='screen'
    )

    return LaunchDescription([
        udp_config_uri_arg,  # <--- [개선] 메인 런치에서 전달받은 UDP 설정 경로 인자 선언
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        use_sim_time_arg,
        #robot_state_publisher_node,
        robot_state_publisher_group,
        spawn_entity_node
    ])


