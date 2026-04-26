#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def generate_launch_description():

    pkg_simulation = get_package_share_directory('dw_simulation')
    # RViz 설정 경로는 더 이상 필요 없으므로 삭제하거나 유지해도 무방합니다.

    # 1. 파라미터 선언
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='-1.6', description='X position of the robot')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='4.0', description='Y position of the robot')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.2', description='Z position of the robot')

    # RViz 대신 Foxglove 사용 여부와 포트 번호 인자 추가
    use_foxglove_arg = DeclareLaunchArgument('use_foxglove', default_value='true', description='Whether to start Foxglove Bridge')
    foxglove_port_arg = DeclareLaunchArgument('foxglove_port', default_value='8765', description='Port for Foxglove Bridge')

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true', description='Whether to use simulation time')

    # 2. 파라미터 값 참조
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')

    use_foxglove = LaunchConfiguration('use_foxglove')
    foxglove_port = LaunchConfiguration('foxglove_port')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # 3. 월드 실행 (start_new_gazebo.launch.py 호출)
    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_simulation, 'launch', 'start_new_gazebo.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # 4. 로봇 스폰 실행 (spawn_robot.launch.py 호출)
    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_simulation, 'launch', 'spawn_robot.launch.py')
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
            'z_pose': z_pose,
            'use_sim_time': use_sim_time
        }.items()
    )

    # 5. Foxglove Bridge 실행 (rviz_node 대체)
    foxglove_node = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        parameters=[{
            'port': foxglove_port,
            'use_sim_time': use_sim_time
        }],
        condition=IfCondition(use_foxglove),
        output='screen'
        # on_exit=Shutdown() # 브리지를 꺼도 시뮬레이션을 유지하고 싶다면 이 줄을 주석 처리하세요.
    )

    return LaunchDescription([
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        use_foxglove_arg,
        foxglove_port_arg,
        use_sim_time_arg,
        world_launch,
        spawn_launch,
        foxglove_node
    ])