import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    pkg_simulation = get_package_share_directory('dw_simulation')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    realsense_share = get_package_share_directory('realsense2_description')
    realsense_model_path = os.path.abspath(os.path.join(realsense_share, '..'))

    pkg_robot_description = get_package_prefix('tb3_description')

    # 1. 인자 선언 및 참조
    use_sim_time = LaunchConfiguration('use_sim_time')
    declare_use_sim_time_cmd = DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation time')
    declare_world_cmd = DeclareLaunchArgument(
        'world',
        # default_value=os.path.join(pkg_simulation, 'worlds', 'turtlebot3_worlds', 'turtlebot3_house.world'),
        default_value=os.path.join(pkg_simulation, 'worlds', 'turtlebot3_worlds', 'test_room_v3.world'),
        description='Full path to the world file to load'
    )

    # 2. Gazebo 파라미터 파일 및 모델 경로 설정
    # 가제보 파라미터 파일 경로 설정 (publish_rate: 100.0 설정 포함)
    gazebo_params_path = os.path.join(pkg_simulation, 'config', 'gazebo_params.yaml')
    gazebo_models_dir = os.path.join(pkg_simulation, 'models')


    # 3. GAZEBO_MODEL_PATH 구성을 위한 리스트 생성
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

    # 4. 환경 변수 병합 헬퍼 함수
    def append_env_path(new_paths, env_var_name):
        existing_path = os.environ.get(env_var_name, '')
        return ':'.join(filter(None, new_paths + [existing_path]))

    env_gazebo_model_path = append_env_path(model_paths, 'GAZEBO_MODEL_PATH')
    env_gazebo_plugin_path = append_env_path([os.path.join(pkg_robot_description, 'lib')], 'GAZEBO_PLUGIN_PATH')
    env_gazebo_resource_path = append_env_path([os.path.join(pkg_robot_description, 'share')], 'GAZEBO_RESOURCE_PATH')

    # 5. Gazebo Server & Client 실행
    # gzserver 실행 시 params_file 강제 주입 (publish_rate 설정 등)
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
        declare_use_sim_time_cmd,
        declare_world_cmd,
        SetEnvironmentVariable('GAZEBO_MODEL_PATH', env_gazebo_model_path),
        SetEnvironmentVariable('GAZEBO_PLUGIN_PATH', env_gazebo_plugin_path),
        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH', env_gazebo_resource_path), 
        gzserver_launch,
        gzclient_launch
    ])
