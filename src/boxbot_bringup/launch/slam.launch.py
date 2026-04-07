import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 1. 패키지 경로 및 설정 파일 경로 지정
    pkg_bringup = get_package_share_directory('boxbot_bringup')
    slam_config_path = os.path.join(pkg_bringup, 'config', 'mapper_params_online_async.yaml')

    # 2. SLAM Toolbox 노드 정의
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node', # 비동기(async) 방식의 맵핑 노드 실행
        name='slam_toolbox',
        output='screen',
        parameters=[
            {'use_sim_time': True}, # 가제보 시뮬레이션을 위해 필수
            slam_config_path,
        ]
    )

    return LaunchDescription([
        slam_node
    ])