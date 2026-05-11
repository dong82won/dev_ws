#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, Shutdown
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # 1. 파라미터 선언 및 참조 (최상위에서 모두 제어 가능하도록 구성)
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_x_pose_cmd = DeclareLaunchArgument('x_pose', default_value='0.0',
                                            description='X position of the robot')
    declare_y_pose_cmd = DeclareLaunchArgument('y_pose', default_value='0.0',
                                            description='Y position of the robot')
    declare_z_pose_cmd = DeclareLaunchArgument('z_pose', default_value='0.2',
                                            description='Z position of the robot')
    declare_use_rviz_cmd = DeclareLaunchArgument('use_rviz', default_value='true',
                                            description='Whether to start RViz')
    declare_use_sim_time_cmd = DeclareLaunchArgument('use_sim_time', default_value='true',
                                            description='Whether to use simulation time')


    # 2. 패키지 경로 참조
    pkg_simulation = get_package_share_directory('dw_simulation')

    # 3. 월드 실행 (Gazebo)
    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_simulation, 'launch', 'start_new_gazebo2.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # 4. 로봇 스폰 및 제어기 실행
    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_simulation, 'launch', 'spawn_robot_ros2_control.launch.py')
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
            'z_pose': z_pose,
            'use_sim_time': use_sim_time
        }.items()
    )

    # 5. RViz 실행
    rviz_config_path = os.path.join(pkg_simulation, 'rviz', 'my_rviz.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path],
        #parameters=[{'use_sim_time': use_sim_time}],
        parameters=[{'use_sim_time': True}], # 강제로 불리언 True 적용
        condition=IfCondition(use_rviz),
        output='screen',
        on_exit=Shutdown()  # RViz가 종료되면 시뮬레이션도 종료
    )

    return LaunchDescription([
        declare_x_pose_cmd,
        declare_y_pose_cmd,
        declare_z_pose_cmd,
        declare_use_rviz_cmd,
        declare_use_sim_time_cmd,
        world_launch,
        spawn_launch,
        rviz_node
    ])