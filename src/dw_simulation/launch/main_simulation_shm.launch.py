#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, Shutdown, SetEnvironmentVariable, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def generate_launch_description():


    pkg_simulation = get_package_share_directory('dw_simulation')
    rviz_config_path = os.path.join(pkg_simulation, 'rviz', 'my_rviz.rviz')

    # --- [개선] config 폴더의 XML 파일 경로를 패키지 기준으로 동적 생성 ---
    shm_config_path = f"file://{os.path.join(pkg_simulation, 'config', 'cycloneDDS_lo_shm.xml')}"
    udp_config_path = f"file://{os.path.join(pkg_simulation, 'config', 'cycloneDDS_lo_udp.xml')}"
    # -------------------------------------------------------------------

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

    # 3. 월드 실행 (전체 기본값이 SHM이므로 가제보는 자동으로 SHM 사용)
    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_simulation, 'launch', 'start_new_gazebo.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )


    # 4. 로봇 스폰 실행 (UDP 설정 경로를 인자로 넘겨줌)
    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_simulation, 'launch', 'spawn_robot_shm.launch.py')
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
            'z_pose': z_pose,
            'use_sim_time': use_sim_time,
            'udp_config_uri': udp_config_path  # <--- [개선] 하위 파일로 UDP 경로 전달
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
    # [수정] GroupAction을 사용하여 RViz에만 UDP 환경을 덮어씌웁니다.
    rviz_group = GroupAction([
        SetEnvironmentVariable('CYCLONEDDS_URI', udp_config_path),
        rviz_node
    ])

    return LaunchDescription([

        # [개선] 전체 시스템의 기본 통신을 SHM으로 설정 (하위 런치 파일에 자동 상속됨)
        SetEnvironmentVariable('CYCLONEDDS_URI', shm_config_path),

        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        use_rviz_arg,
        use_sim_time_arg,
        world_launch,
        spawn_launch,
        #rviz_node
        rviz_group
    ])