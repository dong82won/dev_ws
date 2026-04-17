import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro

from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = 'my_realsense_pkg'
    pkg_share = get_package_share_directory(pkg_name)
    description_pkg_path = get_package_share_directory('realsense2_description')

    params_file = os.path.join(pkg_share, 'config', 'realsense_params2.yaml')

    # 2. URDF/Xacro 처리
    xacro_file = os.path.join(description_pkg_path, 'urdf', 'test_d435i_camera.urdf.xacro')

    robot_description_config = xacro.process_file(xacro_file)
    # xacro 명령어를 통해 URDF 파싱 use_nominal_extrinsics를 false로 주어 URDF가 가짜 IMU TF를 만들지 못하게 막습니다.
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        xacro_file,
        ' use_nominal_extrinsics:=false'
        #' use_nominal_extrinsics:=true' #시뮬레이션용
    ])

    # B. Robot State Publisher (네임스페이스 제거 권장)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'publish_frequency': 30.0,
            'use_tf_static': True,       # 대역폭 절약을 위해 true 권장
            'frame_prefix': "",           # 멀티 로봇이 아니라면 비워둠
            'ignore_timestamp': False,    # 데이터 동기화를 위해 false(기본값) 권장
        }],
        output='screen'
    )

    params_file = os.path.join(pkg_share, 'config', 'realsense_params2.yaml')
    # 3. realsense2_camera 노드
    # 실제 기기 보정값을 읽어와 camera_link 하위의 렌즈 및 IMU TF를 완성하고 데이터를 쏩니다.
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='camera',
        name='realsense_node',
        parameters=[params_file],
        arguments=['--ros-args', '--log-level', 'error'],
        env=dict(os.environ, LRS_LOG_LEVEL='error'),
        output='screen',
        # 🚨 여기에 추가해야 합니다!
        respawn=True,           # 노드가 비정상 종료 시 자동으로 다시 시작
        respawn_delay=2.0,      # 다시 시작하기 전 대기 시간 (초)
    )

    # 4. imu_filter_madgwick 노드
    # RealSense의 Raw IMU를 받아 쿼터니언(방향)을 계산하되, TF는 절대 쏘지 않습니다.
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        output='screen',
        parameters=[params_file],
        remappings=[
            # 필터가 RealSense의 합쳐진 IMU 토픽을 구독하도록 연결
            ('/imu/data_raw', '/camera/realsense_node/imu'),
            # 필터링이 완료된(방향이 포함된) IMU 토픽의 출력 이름
            ('/imu/data', '/imu/filtered')
        ]
    )

    rviz_config_path = os.path.join(pkg_share, 'rviz', 'rviz2.rviz')
    # D. RViz2 실행
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        # name='rviz2',
        # INFO 메시지 차단
        arguments=['-d', rviz_config_path,'--ros-args', '--log-level', 'warn'],
        output='screen'
    )

    # 업로드하신 IMU TF 브로드캐스터 노드
    imu_tf_node = Node(
        package=pkg_name,
        # executable='imu_tf_broadcaster', # setup.py에 등록된 이름
        # executable='imu_tf_watchdog', # setup.py에 등록된 이름
        executable='imu_tf_service', # setup.py에 등록된 이름

        
        name='imu_tf_broadcaster',
        parameters=[params_file],
        output='screen'
    )

    return LaunchDescription([
        realsense_node,
        imu_filter_node,
        imu_tf_node,
        robot_state_publisher,
        rviz_node
    ])