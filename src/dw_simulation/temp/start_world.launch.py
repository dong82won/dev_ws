#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. 패키지 경로 설정
    package_name = 'tb3_simulation'

    pkg_simulation = get_package_share_directory(package_name)
    pkg_prefix = get_package_prefix(package_name)

    # 2. Gazebo 모델 경로 설정 (중요!)
    # 가제보가 패키지 안의 models 폴더와 share 폴더를 인식하게 합니다.
    model_path = os.path.join(pkg_simulation, 'models')
    share_path = os.path.join(pkg_prefix, 'share')

    # 기존 GAZEBO_MODEL_PATH가 있다면 유지하고, 새로운 경로들을 추가합니다.
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += f":{model_path}:{share_path}"
    else:
        os.environ['GAZEBO_MODEL_PATH'] = f"{model_path}:{share_path}"

    # 가제보가 리소스를 찾을 수 있도록 RESOURCE_PATH도 함께 설정하면 더 안전합니다.
    if 'GAZEBO_RESOURCE_PATH' in os.environ:
        os.environ['GAZEBO_RESOURCE_PATH'] += f":{pkg_simulation}"
    else:
        os.environ['GAZEBO_RESOURCE_PATH'] = pkg_simulation

    # 디버깅을 위한 경로 출력 (터미널에서 확인 가능)
    print(f"[DEBUG] GAZEBO_MODEL_PATH: {os.environ['GAZEBO_MODEL_PATH']}")

    # 3. Gazebo 실행 설정 (gazebo_ros의 런치 파일 포함)
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # world 인자 선언 (터미널에서 변경 가능)
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_simulation, 'worlds','my_home_test.world'),
        # 하위 폴더 경로인 'actor_worlds'를 반드시 포함해야 합니다.
        # default_value=os.path.join(pkg_simulation, 'worlds', 'actor_worlds', 'walkbox_bot_empty.world'),
        description='Full path to the world model file to load'
    )

    # gazebo.launch.py 포함
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': LaunchConfiguration('world')}.items()
    )

    return LaunchDescription([
        world_arg,
        gazebo
    ])