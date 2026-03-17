import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # 패키지 이름 설정 (사용자의 패키지명에 맞게 수정하세요)
    package_name = 'boxbot_description'
    pkg_share = get_package_share_directory(package_name)

    # 2. 런치 인자 정의 (실행 시 외부에서 값 변경 가능)
    # 예: ros2 launch ... model:=other_bot.urdf.xacro
    model_arg = DeclareLaunchArgument(
        'model',
        default_value='box_bot3.urdf.xacro',
        description='Name of the robot model file (urdf or xacro)'
    )

    # RViz 설정 파일 경로 [cite: 10]
    default_rviz_config_path = PathJoinSubstitution([pkg_share, 'rviz', 'urdf_vis.rviz'])
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config_path,
        description='Absolute path to rviz config file'
    )

    # rviz_config_arg = DeclareLaunchArgument(
    #     'rviz_config',
    #     default_value=os.path.join(pkg_share, 'rviz', 'urdf_vis.rviz'),
    #     description='Path to RViz config file'
    # )

    # 로봇 모델 처리 (Xacro/URDF 통합 대응)
    # ParameterValue를 사용하면 XML 데이터를 보다 안정적으로 노드에 전달합니다.
    robot_description_content = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([pkg_share, 'urdf', LaunchConfiguration('model')])]),
        value_type=str
    )

    # # Xacro 파일 경로 설정
    # xacro_file = os.path.join(pkg_share, 'urdf', 'box_bot3.urdf.xacro')
    # # 로봇 모델 처리 (Xacro -> URDF 문자열 변환)
    # robot_description_content = ParameterValue( Command(['xacro ', xacro_file]),
    #     value_type=str
    # )

    # 3. 로봇 상태 발행 노드
    # URDF 데이터를 /robot_description 토픽으로 발행합니다.
    # robot_state_publisher: URDF 데이터를 TF로 변환
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': False  # Gazebo가 없으므로 시스템 시간을 사용합니다.
        }]
    )

    # 4. 조인트 상태 발행 노드 (GUI 포함)
    # joint_state_publisher_gui: 관절 제어 슬라이더 제공
    # Gazebo 플러그인이 없으므로, GUI를 통해 수동으로 조인트를 움직여볼 수 있습니다.
    joint_state_publisher_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        # [추가 1] 실행 로그를 터미널에서 확인
        output='screen',
        # [추가 2] Gazebo가 없으므로 시스템 시간 사용
        parameters=[{'use_sim_time': False }]
    )

    # rviz2: 시각화
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        parameters=[{'use_sim_time': False}],
        output='screen'
    )

    return LaunchDescription([
        model_arg,
        rviz_config_arg,
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node
    ])