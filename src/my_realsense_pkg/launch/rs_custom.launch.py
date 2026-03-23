import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro

def generate_launch_description():
    # 경로 설정
    pkg_dir = get_package_share_directory('my_realsense_pkg')
    params_file = os.path.join(pkg_dir, 'config', 'realsense_params.yaml')

    # 1. RealSense 노드 (환경변수로 하드웨어 로그 차단)
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='front_camera',  # YAML과 일치
        name='camera',             # YAML과 일치
        parameters=[params_file],
        output='screen',
        arguments=['--ros-args', '--log-level', 'error'],
        env=dict(os.environ, LRS_LOG_LEVEL='error')
    )

    # 2. Robot State Publisher (TF 생성용)
    desc_pkg_path = get_package_share_directory('realsense2_description')
    xacro_file = os.path.join(desc_pkg_path, 'urdf', 'test_d435i_camera.urdf.xacro')

    # xacro 파일을 프로세싱합니다.
    robot_description_config = xacro.process_file(xacro_file)

    # 💡 해결책: .toxml() 대신 아래와 같이 작성해 보세요.
    # 일부 버전에서는 doc 속성을 통해 접근해야 하거나, 직접 문자열로 변환해야 합니다.
    # robot_desc = robot_description_config.toprettyxml(indent='  ')
    robot_desc = robot_description_config.toxml() # type: ignore


    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}],
        output='screen'
    )

    # ===============================================================
    # 4. IMU Filter (핵심: orientation → TF 생성)
    # ===============================================================
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        parameters=[{
            'use_mag': False,
            # 🔥 TF 생성 핵심 설정
            'publish_tf': True,
            'world_frame': 'enu',        # RViz Fixed Frame
            'fixed_frame': 'base_link', # 회전 대상 (URDF와 반드시 일치)
            'reverse_tf': False,

            # 'constant_dt': 0.0,
            # 'stateless': False
        }],
        remappings=[
            ('/imu/data_raw', '/front_camera/camera/imu')
        ],
        output='screen'
    )

    rviz_config_dir = os.path.join(pkg_dir, 'rviz', 'urdf_vis.rviz')
    # 4. RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        # name='rviz2',
        arguments=['-d', rviz_config_dir],
        output='screen'
    )

    return LaunchDescription([
        realsense_node,
        robot_state_publisher,
        imu_filter_node,
        rviz_node
    ])