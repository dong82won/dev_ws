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
    rviz_config_path = os.path.join(pkg_simulation, 'rviz', 'my_rviz.rviz')

    # 1. 파라미터 선언 (최상위에서 모두 제어 가능하도록 구성)
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='-1.6', description='X position of the robot')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='4.0', description='Y position of the robot')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.2', description='Z position of the robot')

    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='true', description='Whether to start RViz')
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true', description='Whether to use simulation time')

    # 2. 파라미터 값 참조
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # 3. 월드 실행 (start_world2.launch.py 호출)
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

    # 5. RViz 실행
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
        output='screen',
        on_exit=Shutdown()  # RViz가 종료되면 시뮬레이션도 종료
    )

    return LaunchDescription([
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        use_rviz_arg,
        use_sim_time_arg,
        world_launch,
        spawn_launch,
        rviz_node
    ])