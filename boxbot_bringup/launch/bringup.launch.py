import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 1. 패키지의 설치된 공유 디렉토리(share) 경로를 가져옵니다.
    # 이 경로는 보통 ~/ros2_ws/install/boxbot_bringup/share/boxbot_bringup 가 됩니다.
    pkg_bringup = get_package_share_directory('boxbot_bringup')

    # 2. Localization (EKF) 런치 파일 포함 (pkg_bringup 변수 사용)
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'localization.launch.py')
        )
    )

    # 3. SLAM Toolbox 런치 파일 포함 (pkg_bringup 변수 사용)
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'slam.launch.py')
        )
    )

    return LaunchDescription([
        localization_launch,
        slam_launch
    ])