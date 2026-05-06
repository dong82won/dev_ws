import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. 패키지 공유 디렉토리 경로 가져오기
    pkg_share = get_package_share_directory('boxbot_bringup')

    # 2. 설정 파일 경로 세팅
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf.yaml')
    diag_config_path = os.path.join(pkg_share, 'config', 'diagnostics.yaml') # [추가] 진단 설정 파일 경로

    # 상위에서 넘겨준 값을 받거나 없으면 기본값 사용
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # 3. robot_localization (EKF) 노드 정의
    localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': use_sim_time}]
    )

    # 4. [추가] diagnostic_aggregator 노드 정의
    diagnostic_aggregator_node = Node(
        package='diagnostic_aggregator',
        executable='aggregator_node',
        name='diagnostic_aggregator',
        output='screen',
        parameters=[diag_config_path, {'use_sim_time': use_sim_time}]
    )

    # 5. 실행할 노드 목록에 두 개 모두 반환
    return LaunchDescription([
        localization_node,
        diagnostic_aggregator_node  # 배열에 추가
    ])