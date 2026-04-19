import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():


    # 2. Realsense 패키지 경로 탐색 (가제보 렌더링용)
    try:
        realsense_share = get_package_share_directory('realsense2_description')
        # install/realsense2_description 경로를 확보하여 가제보가 package://를 해석하게 함
        realsense_model_path = os.path.abspath(os.path.join(realsense_share, '..'))
    except Exception:
        realsense_model_path = ''

    # 3. 모델 경로 통합
    # 1. 패키지 경로 설정
    pkg_robot_description = get_package_prefix('turtlebot3_description')

    pkg_simulation = get_package_share_directory('dw_simulation')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    gazebo_models_dir = os.path.join(pkg_simulation, 'models')
    model_path_list = [
        os.path.join(pkg_robot_description, 'share'),
        gazebo_models_dir,
        realsense_model_path
    ]

    # 추가 모델 디렉토리 탐색
    if os.path.exists(gazebo_models_dir):
        for item in os.listdir(gazebo_models_dir):
            full_path = os.path.join(gazebo_models_dir, item)
            if os.path.isdir(full_path) and not os.path.exists(os.path.join(full_path, 'model.config')):
                model_path_list.append(full_path)

    combined_model_path = ':'.join([p for p in model_path_list if p])

    # 4. 가제보 실행 설정
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_simulation, 'worlds', 'turtlebot3_worlds', 'turtlebot3_house.world'),
        description='Full path to world file'
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    return LaunchDescription([
        # gzserver가 실행되기 전에 환경 변수 선언
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', f"{combined_model_path}:{os.environ.get('GAZEBO_MODEL_PATH', '')}"),
        SetEnvironmentVariable('GAZEBO_PLUGIN_PATH', f"{os.path.join(pkg_robot_description, 'lib')}:{os.environ.get('GAZEBO_PLUGIN_PATH', '')}"),
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', f"{os.path.join(pkg_robot_description, 'share')}:{os.environ.get('GAZEBO_RESOURCE_PATH', '')}"),
        world_arg,
        gazebo
    ])