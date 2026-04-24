import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. 패키지 경로 설정
    realsense_share = get_package_share_directory('realsense2_description')
    realsense_model_path = os.path.abspath(os.path.join(realsense_share, '..'))

    pkg_simulation = get_package_share_directory('dw_simulation')
    pkg_robot_description = get_package_prefix('tb3_description')

    gazebo_models_dir = os.path.join(pkg_simulation, 'models')

    # 2. GAZEBO_MODEL_PATH 구성을 위한 리스트 생성
    model_paths = [
        os.path.join(pkg_robot_description, 'share'),
        gazebo_models_dir,
        realsense_model_path
    ]

    # 추가 모델 디렉토리 탐색 (카테고리 폴더 처리)
    if os.path.exists(gazebo_models_dir):
        for item in os.listdir(gazebo_models_dir):
            full_path = os.path.join(gazebo_models_dir, item)
            # 디렉토리이면서 내부에 model.config가 없는 경우 (하위 폴더들을 포함하는 루트 폴더로 간주)
            if os.path.isdir(full_path) and not os.path.exists(os.path.join(full_path, 'model.config')):
                model_paths.append(full_path)

    # 3. 환경 변수 병합 헬퍼 함수 (중복 콜론 방지 및 깔끔한 결합)
    def append_env_path(new_paths, env_var_name):
        existing_path = os.environ.get(env_var_name, '')
        # filter(None, ...)을 사용하여 빈 문자열을 걸러내고 ':'로 연결
        return ':'.join(filter(None, new_paths + [existing_path]))

    # 환경 변수 문자열 생성
    env_gazebo_model_path = append_env_path(model_paths, 'GAZEBO_MODEL_PATH')
    env_gazebo_plugin_path = append_env_path([os.path.join(pkg_robot_description, 'lib')], 'GAZEBO_PLUGIN_PATH')
    env_gazebo_resource_path = append_env_path([os.path.join(pkg_robot_description, 'share')], 'GAZEBO_RESOURCE_PATH')

    # 4. 가제보 실행 설정 (Launch Arguments)
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_simulation, 'worlds', 'turtlebot3_worlds', 'turtlebot3_house.world'),
        description='Full path to the world file to load'
    )

    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    # 5. LaunchDescription 반환
    return LaunchDescription([
        # 환경 변수 설정
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', env_gazebo_model_path),
        SetEnvironmentVariable('GAZEBO_PLUGIN_PATH', env_gazebo_plugin_path),
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', env_gazebo_resource_path),

        # Argument 및 노드(Include) 실행
        world_arg,
        gazebo_launch
    ])