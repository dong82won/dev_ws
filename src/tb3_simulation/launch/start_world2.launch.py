#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. 패키지 경로 설정
    pkg_description = "boxbot_description"
    install_dir = get_package_prefix(pkg_description)

    pkg_simulation = get_package_share_directory('tb3_simulation')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # 2. Realsense 패키지 예외 처리
    try:
        pkg_realsense_share = get_package_share_directory('realsense2_description')
        pkg_realsense_dir = os.path.abspath(os.path.join(pkg_realsense_share, '..'))
    except PackageNotFoundError:
        pkg_realsense_dir = ""

    # 3. 모델 경로 스캔 로직
    gazebo_models_dir = os.path.join(pkg_simulation, 'models')
    # share 디렉토리들을 리스트에 담습니다.
    model_path_list = [
        os.path.join(install_dir, 'share'), 
        gazebo_models_dir, 
        pkg_realsense_dir
    ]

    if os.path.exists(gazebo_models_dir):
        for item in os.listdir(gazebo_models_dir):
            full_path = os.path.join(gazebo_models_dir, item)
            if os.path.isdir(full_path) and not os.path.exists(os.path.join(full_path, 'model.config')):
                model_path_list.append(full_path)

    combined_model_path = ':'.join([p for p in model_path_list if p])

    # 4. 플러그인 및 리소스 경로 설정
    plugin_path = os.path.join(install_dir, 'lib')
    
    # [수정] 여러 패키지의 share 경로를 포함하여 메쉬 누락을 방지합니다.
    # pkg_simulation의 상위 디렉토리(share)도 포함시킵니다.
    resource_paths = [
        os.path.join(install_dir, 'share'),
        os.path.abspath(os.path.join(pkg_simulation, '..'))
    ]
    combined_resource_path = ':'.join(resource_paths)

    # 5. Gazebo 실행 설정
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_simulation, 'worlds', 'turtlebot3_worlds', 'turtlebot3_world.world'),
        description='Full path to the world model file to load'
    )

    return LaunchDescription([
        SetEnvironmentVariable('GAZEBO_MODEL_PATH',
            [combined_model_path, ':', os.environ.get('GAZEBO_MODEL_PATH', '')]),

        SetEnvironmentVariable('GAZEBO_PLUGIN_PATH',
            [plugin_path, ':', os.environ.get('GAZEBO_PLUGIN_PATH', '')]),

        SetEnvironmentVariable('GAZEBO_RESOURCE_PATH',
            [combined_resource_path, ':', os.environ.get('GAZEBO_RESOURCE_PATH', '')]),

        world_arg,
        gazebo
    ])