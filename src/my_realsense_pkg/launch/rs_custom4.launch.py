import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro

from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = 'my_realsense_pkg'
    pkg_share = get_package_share_directory(pkg_name)
    description_pkg_path = get_package_share_directory('realsense2_description')

    params_file = os.path.join(pkg_share, 'config', 'realsense_params2.yaml')

    # 2. URDF/Xacro 처리
    xacro_file = os.path.join(description_pkg_path, 'urdf', 'test_d435i_camera.urdf.xacro')

    robot_description_config = xacro.process_file(xacro_file)
    # xacro 명령어를 통해 URDF 파싱 use_nominal_extrinsics를 false로 주어 URDF가 가짜 IMU TF를 만들지 못하게 막습니다.
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        xacro_file,
        ' use_nominal_extrinsics:=false'
        #' use_nominal_extrinsics:=true' #시뮬레이션용
    ])

    # B. Robot State Publisher (네임스페이스 제거 권장)
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'publish_frequency': 30.0,
            'use_tf_static': True,       # 대역폭 절약을 위해 true 권장
            'frame_prefix': "",           # 멀티 로봇이 아니라면 비워둠
            'ignore_timestamp': False,    # 데이터 동기화를 위해 false(기본값) 권장
        }],
        output='screen'
    )


    params_file = os.path.join(pkg_share, 'config', 'realsense_params2.yaml')
    # 3. realsense2_camera 노드
    # 실제 기기 보정값을 읽어와 camera_link 하위의 렌즈 및 IMU TF를 완성하고 데이터를 쏩니다.
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='camera',
        name='realsense_node',
        # parameters=[{
        #     'enable_gyro': True,            # 자이로스코프 켜기
        #     'enable_accel': True,           # 가속도계 켜기
        #     'unite_imu_method': 2,          # 중요: accel과 gyro를 하나의 /camera/imu 토픽으로 합침 (2 = linear_interpolation)
        #     'enable_sync': True,            # 이미지와 IMU 데이터의 타임스탬프 동기화
        #     'publish_tf': True,             # 기본값이지만, 카메라 내부 TF를 쏘도록 확실히 활성화
        #     'pointcloud.enable': True,           # 3D 점군 데이터 발행
        #     'pointcloud.ordered_pc': False,      # 정렬된 점군 여부
        #     'pointcloud.stream_filter': 2       # <--- 이 줄을 추가하세요! (2번은 Color를 의미함)
        # }],
        parameters=[params_file],
        output='screen',
    )

    # 4. imu_filter_madgwick 노드
    # RealSense의 Raw IMU를 받아 쿼터니언(방향)을 계산하되, TF는 절대 쏘지 않습니다.
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        output='screen',
        # parameters=[{
        #     'use_mag': False,               # 필수: D435i에는 지자기 센서가 없으므로 끕니다.
        #     'publish_tf': False,            # 필수: 기존 TF 트리를 망치지 않도록 필터 자체의 TF 발행을 끕니다.
        #     'world_frame': 'enu',            # ROS 표준 좌표계(East-North-Up) 사용
        #     # 'fixed_frame': 'odom',
        #     # 'base_frame': 'base_link',   # RSP의 base_link와 
        # }],
        parameters=[params_file],
        remappings=[
            # 필터가 RealSense의 합쳐진 IMU 토픽을 구독하도록 연결
            ('/imu/data_raw', '/camera/realsense_node/imu'), 
            # 필터링이 완료된(방향이 포함된) IMU 토픽의 출력 이름
            ('/imu/data', '/imu/filtered') 
        ]
    )
    
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'rviz2.rviz')
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