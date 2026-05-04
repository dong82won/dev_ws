import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    
    # 1. 시뮬레이션 시간 설정 인자 선언
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation time'
    )
    use_sim_time = LaunchConfiguration('use_sim_time')

    # 2. 가제보 파라미터 파일 경로 설정 (publish_rate: 100.0 설정 포함)
    # 이 파일이 ~/dev_ws/src/boxbot_bringup/config/gazebo_params.yaml 에 있어야 합니다.
    pkg_bringup = get_package_share_directory('boxbot_bringup')
    gazebo_params_path = os.path.join(pkg_bringup, 'config', 'gazebo_params.yaml')

    # 3. 패키지 및 모델 경로 설정 (사용자님 기존 로직 유지)
    realsense_share = get_package_share_directory('realsense2_description')
    realsense_model_path = os.path.abspath(os.path.join(realsense_share, '..'))

    pkg_simulation = get_package_share_directory('dw_simulation')
    pkg_robot_description = get_package_prefix('tb3_description')

    gazebo_models_dir = os.path.join(pkg_simulation, 'models') 

    # 4. GAZEBO_MODEL_PATH 구성을 위한 리스트 생성
    model_paths = [
        os.path.join(pkg_robot_description, 'share'),
        gazebo_models_dir,
        realsense_model_path
    ]

    # 추가 모델 디렉토리 탐색 (카테고리 폴더 처리)
    if os.path.exists(gazebo_models_dir):
        for item in os.listdir(gazebo_models_dir):
            full_path = os.path.join(gazebo_models_dir, item)
            if os.path.isdir(full_path) and not os.path.exists(os.path.join(full_path, 'model.config')):
                model_paths.append(full_path)

    # 5. 환경 변수 병합 헬퍼 함수
    def append_env_path(new_paths, env_var_name):
        existing_path = os.environ.get(env_var_name, '')
        return ':'.join(filter(None, new_paths + [existing_path]))

    env_gazebo_model_path = append_env_path(model_paths, 'GAZEBO_MODEL_PATH')
    env_gazebo_plugin_path = append_env_path([os.path.join(pkg_robot_description, 'lib')], 'GAZEBO_PLUGIN_PATH')
    env_gazebo_resource_path = append_env_path([os.path.join(pkg_robot_description, 'share')], 'GAZEBO_RESOURCE_PATH')

    # 6. 월드 파일 인자 선언
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_simulation, 'worlds', 'turtlebot3_worlds', 'turtlebot3_house.world'),
        description='Full path to the world file to load'
    )
    # 7. 가제보 서버(gzserver) 및 클라이언트(gzclient) 분리 실행
    # gzserver 실행 시 params_file을 주입하여 publish_rate 설정을 확실히 적용합니다.
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    gzserver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'use_sim_time': use_sim_time,
            'params_file': gazebo_params_path  # ★ 핵심: 파라미터 파일 강제 주입
        }.items()
    )

    gzclient_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time
        }.items()
    )
    # 8. 최종 실행 구성 반환
    return LaunchDescription([
        use_sim_time_arg,
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', env_gazebo_model_path),
        SetEnvironmentVariable('GAZEBO_PLUGIN_PATH', env_gazebo_plugin_path),
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', env_gazebo_resource_path),
        world_arg,
        gzserver_launch,
        gzclient_launch
    ])
