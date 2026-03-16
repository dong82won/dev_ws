#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration # [추가된 Import]

def generate_launch_description():
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    pkg_simulation = get_package_share_directory('boxbot_simulation')
    # pkg_small_house = get_package_share_directory('aws_robomaker_small_house_world')
    # pkg_gazebo_collection = get_package_share_directory('gazebo_models_worlds_collection')

    try:
        # realsense2_description 패키지의 share 경로를 가져옴
        pkg_realsense_share = get_package_share_directory('realsense2_description')
        # Gazebo가 패키지 이름을 찾을 수 있도록 상위 디렉토리(share)를 지정
        pkg_realsense_dir = os.path.abspath(os.path.join(pkg_realsense_share, '..'))
    except PackageNotFoundError:
        print("----------------------------------------------------------------")
        print("WARNING: realsense2_description package not found!")
        print("----------------------------------------------------------------")
        pkg_realsense_dir = ""

    # 모델 경로 설정을 위한 준비
    pkg_description = "boxbot_description"
    install_dir = get_package_prefix(pkg_description)

    # 모델 경로들
    gazebo_models_dir = os.path.join(pkg_simulation, 'models')
    # house_models_dir = os.path.join(pkg_small_house, 'models')
    # gazebo_collection_dir = os.path.join(pkg_small_house, 'models')

    # 환경 변수 추가 (기존 경로 유지 + 새 경로 추가)
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += f":{install_dir}/share:{gazebo_models_dir}:{pkg_realsense_dir}"
    else:
        os.environ['GAZEBO_MODEL_PATH'] = f"{install_dir}/share:{gazebo_models_dir}:{pkg_realsense_dir}"

    if 'GAZEBO_PLUGIN_PATH' in os.environ:
        os.environ['GAZEBO_PLUGIN_PATH'] += f":{install_dir}/lib"
    else:
        os.environ['GAZEBO_PLUGIN_PATH'] = f"{install_dir}/lib"

    print(f"GAZEBO MODELS PATH: {os.environ['GAZEBO_MODEL_PATH']}")
    print(f"GAZEBO PLUGINS PATH: {os.environ['GAZEBO_PLUGIN_PATH']}")

    # Gazebo 실행
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(pkg_simulation, 'worlds', 'box_bot_empty2.world'),
            description='Full path to the world model file to load'),
            gazebo
    ])


