import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_name = 'my_realsense_pkg' 
    pkg_share = get_package_share_directory(pkg_name)
    description_pkg_path = get_package_share_directory('realsense2_description')
    
    params_file = os.path.join(pkg_share, 'config', 'realsense_params2.yaml')
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'rviz2.rviz')

    # 2. URDF/Xacro 처리
    xacro_file = os.path.join(description_pkg_path, 'urdf', 'test_d435i_camera.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)

    # 3. 노드 구성 정의
    
    # A. RealSense 카메라 노드
    realsense_node = Node(
        package='realsense2_camera',
        namespace='camera',
        executable='realsense2_camera_node',
        name='camera',
        parameters=[params_file],
        output='screen'
    )

    # B. Robot State Publisher (네임스페이스 제거 권장)
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        # namespace='camera', # 제거: base_link 이름을 순수하게 유지하기 위함
        parameters=[{
            'robot_description': robot_description_config.toxml(), # type: ignore
            'publish_frequency': 30.0
        }],
        output='screen'
    )

    # C. IMU Madgwick 필터 노드
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        # namespace='camera', # 제거 또는 유지 (RSP와 맞추는 것이 중요)
        parameters=[{
            'use_mag': False,
            'publish_tf': True,
            'fixed_frame': 'odom',
            'base_frame': 'base_link',   # RSP의 base_link와 이름이 완벽히 일치해야 함
            'use_header_frame_id': False, # <--- 이 설정을 추가하여 헤더의 'camera_imu_optical_frame' 무시
            'gain': 0.1,
            'stateless': False           # 초기 방향 설정을 위해 False 권장                  
        }],
        remappings=[
            ('/imu/data_raw', '/camera/camera/imu'), 
            ('/imu/data', '/camera/imu/filtered')
        ],
        output='screen'
    )

    # D. RViz2 실행
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )

    return LaunchDescription([
        realsense_node,
        imu_filter_node,        
        rsp_node,        
        rviz_node
    ])