import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, LifecycleNode  # 💡 LifecycleNode 임포트
import xacro

# 생명주기 제어를 위한 이벤트 핸들러 임포트
from launch.actions import EmitEvent, RegisterEventHandler
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
import lifecycle_msgs.msg


def generate_launch_description():
    pkg_name = 'my_realsense_pkg'
    pkg_share = get_package_share_directory(pkg_name)
    description_pkg_path = get_package_share_directory('realsense2_description')

    # 업데이트된 파라미터 파일 경로 반영
    params_file = os.path.join(pkg_share, 'config', 'realsense_params2_update.yaml')

    # 2. URDF/Xacro 처리
    xacro_file = os.path.join(description_pkg_path, 'urdf', 'test_d435i_camera.urdf.xacro')
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        xacro_file,
        ' use_nominal_extrinsics:=false'
    ])

    # A. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
            'publish_frequency': 30.0,
            'use_tf_static': True,
            'frame_prefix': "",
            'ignore_timestamp': False,
        }],
        output='screen',
        # ⭐ TF 리매핑 수정: 전역으로 깔끔하게 일치시킵니다.
        remappings=[
            ('tf', '/tf'),
            ('tf_static', '/tf_static')
        ],
    )

    # 3. realsense2_camera 노드 (💡 LifecycleNode로 변경)
    realsense_node = LifecycleNode(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='camera',
        name='realsense_node',
        parameters=[params_file],
        arguments=['--ros-args', '--log-level', 'error'],
        env=dict(os.environ, LRS_LOG_LEVEL='error'),
        output='screen',
        # ⚠️ LifecycleNode 액션은 기본 respawn을 다르게 처리하므로 에러 방지를 위해 제외합니다.
        # ⭐ TF 리매핑 중요 수정: 네임스페이스 안의 상대경로 'tf'를 전역 '/tf'로 강제 리매핑합니다.
        remappings=[
            ('tf', '/tf'),
            ('tf_static', '/tf_static')
        ]
    )

    # 4. imu_filter_madgwick 노드
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        output='screen',
        parameters=[
            params_file,
            {'use_mag': False}  # 💡 지자기 센서가 없는 리얼센스를 위해 필터가 멈추는 현상 방지
        ],
        remappings=[
            # 💡 기존 '/camera/camera/imu' 에서 아래 이름으로 변경합니다!
            ('/imu/data_raw', '/camera/realsense_node/imu'),
            ('/imu/data', '/imu/filtered')
        ]
    )

    # C. RViz2 실행
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'realsense_view.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path, '--ros-args', '--log-level', 'warn'],
        output='screen'
    )

    # D. 업로드하신 IMU TF 브로드캐스터 노드 (일반 노드로 유지)
    imu_tf_node = Node(
        package=pkg_name,
        executable='imu_tf_service',  # setup.py에 등록된 실행 파일 이름
        name='imu_tf_broadcaster',
        parameters=[params_file],
        output='screen'
    )

    # -------------------------------------------------------------------------
    # 🔄 RealSense 라이프사이클 노드 자동 활성화(State Transition) 트리거 정의
    # ------------------------------------------------------------------------- 
    # 카메라인 'realsense_node'가 켜지면 자동으로 Configure 실행
    trigger_realsense_configure = EmitEvent(
        event=ChangeState(
            # 💡 매개변수 이름을 lifecycle_node_matcher로 변경하고 lambda 식을 주입합니다.
            lifecycle_node_matcher=lambda node: node == realsense_node,
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    # Configure가 완료되어 inactive 상태가 되면 자동으로 Activate 실행 (최종 작동 시작)
    trigger_realsense_activate = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=realsense_node,
            start_state='unconfigured',
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        # 💡 여기도 동일하게 매칭 인자 명칭과 lambda 식을 적용합니다.
                        lifecycle_node_matcher=lambda node: node == realsense_node,
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )
                )
            ],
        )
    )

    # -------------------------------------------------------------------------
    # 최종 실행 대상 리스트 반환
    # -------------------------------------------------------------------------
    return LaunchDescription([
        realsense_node,
        imu_filter_node,
        imu_tf_node,
        robot_state_publisher,
        rviz_node,

        # 라이프사이클 작동용 자동 트리거 추가
        trigger_realsense_configure,
        trigger_realsense_activate
    ])