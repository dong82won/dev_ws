import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. 패키지 경로 설정
    package_name = 'tb3_simulation'
    pkg_simulation = get_package_share_directory(package_name)
    pkg_prefix = get_package_prefix(package_name)

    # 2. Gazebo 모델 경로 설정 (계층 구조 해결)
    models_path = os.path.join(pkg_simulation, 'models')

    # [수정 핵심] models 폴더와 그 아래 모든 1단계 하위 폴더들을 리스트에 넣습니다.
    # 예: ['.../models', '.../models/Photo_models', '.../models/QR_models']
    model_path_list = [models_path]
    if os.path.exists(models_path):
        for item in os.listdir(models_path):
            full_path = os.path.join(models_path, item)
            if os.path.isdir(full_path):
                model_path_list.append(full_path)

    # 리스트를 콜론(:)으로 연결하여 하나의 문자열로 만듭니다.
    combined_model_path = ':'.join(model_path_list)

    # 기존 환경변수가 있다면 병합 (share 경로 포함)
    share_path = os.path.join(pkg_prefix, 'share') 
    plugin_path = os.path.join(pkg_prefix, 'lib')

    if 'GAZEBO_MODEL_PATH' in os.environ:
        final_model_path = f"{combined_model_path}:{share_path}:{os.environ['GAZEBO_MODEL_PATH']}"
    else:
        final_model_path = f"{combined_model_path}:{share_path}"

    if 'GAZEBO_PLUGIN_PATH' in os.environ:
        os.environ['GAZEBO_PLUGIN_PATH'] += f":{plugin_path}"
    else:
        os.environ['GAZEBO_PLUGIN_PATH'] = f"{plugin_path}"


    # 3. Gazebo 실행 설정
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    world_arg = DeclareLaunchArgument(
        'world',
        # 파일 구조상 worlds/actor_worlds 경로 확인 필요
        default_value=os.path.join(pkg_simulation, 'worlds', 'actor_worlds', 'walk_and_sit.world'),
        description='Full path to the world model file to load'
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    return LaunchDescription([
        # os.environ 수정 대신 ROS2 공식 액션인 SetEnvironmentVariable 사용 권장
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', final_model_path),
        # RESOURCE_PATH 설정 (텍스처 로딩 등을 위해 필요)
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', f"{pkg_simulation}:{os.environ.get('GAZEBO_RESOURCE_PATH', '')}"),

        
        world_arg,
        gazebo
    ])