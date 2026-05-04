import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. 패키지의 설치된 공유 디렉토리(share) 경로를 가져옵니다.
    # 이 경로는 보통 ~/ros2_ws/install/boxbot_bringup/share/boxbot_bringup 가 됩니다.
    pkg_bringup = get_package_share_directory('boxbot_bringup')

    # 1. 인자 선언 (기본값 true) 
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', 
        default_value='true',
        description='Use simulation time'
    )

    # 2. Localization (EKF) - 수정됨
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'localization.launch.py') # 여기서 괄호 닫기!
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items() # IncludeLaunchDescription의 인자로 이동
    )

    # 3. SLAM Toolbox - 수정됨
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'slam.launch.py') # 여기서 괄호 닫기!
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items() # IncludeLaunchDescription의 인자로 이동
    )

    return LaunchDescription([
        use_sim_time_arg, # 추가
        localization_launch,
        slam_launch
    ])