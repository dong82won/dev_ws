import os
import subprocess
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro

def generate_launch_description():
    # 1. 경로 설정
    pkg_name = 'my_realsense_pkg'  # 사용자 패키지 이름
    pkg_dir = get_package_share_directory(pkg_name)
    params_file = os.path.join(pkg_dir, 'config', 'realsense_params.yaml')
    rviz_config_path = os.path.join(pkg_dir, 'rviz', 'urdf_vis.rviz')

    # 2. RealSense 노드 (IMU 데이터 발행 핵심)
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='front_camera',
        name='camera',
        parameters=[params_file],
        output='screen',
        arguments=['--ros-args', '--log-level', 'error'],
        env=dict(os.environ, LRS_LOG_LEVEL='error')
    )

    # 3. Robot State Publisher (카메라 모델 로드)
    desc_pkg_path = get_package_share_directory('realsense2_description')
    xacro_file = os.path.join(desc_pkg_path, 'urdf', 'test_d435i_camera.urdf.xacro')
    robot_desc = subprocess.check_output(['xacro', xacro_file]).decode('utf-8')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}],
        output='screen'
    )

    # 4. IMU Filter Madgwick (트리 연결의 핵심)
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        
        parameters=[{
            'gain': 0.05,
            'use_mag': False,
            'publish_tf': False,
            'world_frame': "enu",
            'fixed_frame': "odom",
            'stateless': False,

            # 초기 자세를 즉시 잡을지 여부
            # 'gain': 0.1,
            # 'use_sensor_data': True,  # 🔥 핵심: Best Effort QoS를 사용하도록 설정
            # # 추가: 데이터의 실제 좌표계를 명시적으로 알려줌
            # 'publish_debug_topics': True,
            # 'constant_dt': 0.005,      # 데이터 주기를 자동 계산
            # 'orientation_stddev': 0.0,
            # 'remove_gravity_vector': False,
            # 'stateless': True       # 초기 정지 상태 확인 여부
        }],

        remappings=[
            ('/imu/data_raw', '/front_camera/camera/imu'),
            ('/imu/data', '/front_camera/camera/imu/filtered')
        ],
        output='screen'
    )

    # 5. RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )

    return LaunchDescription([
        realsense_node,
        robot_state_publisher,
        imu_filter_node,
        rviz_node,
  
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     name='odom_to_enu_bridge',
        #     arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link']
        # ),
        # Node(
        #     package='tf2_ros',
        #     executable='static_transform_publisher',
        #     arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'camera_imu_optical_frame']
        #     )

    ])