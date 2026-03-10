import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 1. 패키지 공유 디렉토리 경로 가져오기
    pkg_share = get_package_share_directory('boxbot_bringup')

    # 2. EKF 설정 파일 경로 설정
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf.yaml')

    # 3. robot_localization (EKF) 노드 정의
    localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': True}]
    )

    return LaunchDescription([
        localization_node
    ])