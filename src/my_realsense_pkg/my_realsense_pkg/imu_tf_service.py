#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_srvs.srv import Empty  # 리셋 서비스를 위한 임포트
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import tf_transformations
import numpy as np

class ImuTFBroadcaster(Node):
    def __init__(self):
        super().__init__('imu_tf_watchdog')

        # 1. 상태 변수 및 파라미터 설정
        self.declare_parameter('q_offset', [0.5, -0.5, 0.5, 0.5])
        self.q_offset = self.get_parameter('q_offset').get_parameter_value().double_array_value
        
        self.last_msg_time = self.get_clock().now()
        self.data_received_once = False
        self.is_resetting = False  # 리셋 중 중복 호출 방지
        
        self.callback_count = 0
        self.skip_count = 4  # 200Hz -> 50Hz 다운샘플링
        self.reset_timeout = 5.0  # 데이터 중단 판단 임계값 (초)

        # 2. 서비스 클라이언트 설정 (RealSense 하드웨어 리셋)
        # 서비스 이름은 환경에 따라 '/camera/camera/device_reset' 등으로 확인 필요
        self.reset_client = self.create_client(Empty, '/camera/camera/device_reset')

        # 3. TF 브로드캐스터 및 구독 설정
        self.br = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Imu, 
            '/imu/filtered', 
            self.imu_callback, 
            10
        )

        # 4. 감시 타이머 (1.0초마다 체크)
        self.health_check_timer = self.create_timer(1.0, self.check_data_health)
        
        self.get_logger().info(f'🚀 리셋 기능이 통합된 IMU TF 노드 시작 (다운샘플링: 1/{self.skip_count})')

    def check_data_health(self):
        """데이터가 정상적으로 들어오고 있는지 검사하고 필요시 리셋 호출"""
        if self.is_resetting:
            return

        now = self.get_clock().now()
        elapsed_time = (now - self.last_msg_time).nanoseconds / 1e9

        if not self.data_received_once:
            self.get_logger().warn('데이터 수신 대기 중...', throttle_duration_sec=5.0)
        elif elapsed_time > self.reset_timeout:
            self.get_logger().error(f'⚠️ IMU 데이터 중단 감지! ({elapsed_time:.1f}초 경과). 센서 리셋을 시도합니다...')
            self.call_reset_service()

    def call_reset_service(self):
        """RealSense 노드에 하드웨어 리셋 서비스를 비동기로 요청"""
        if not self.reset_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().error('❌ 리셋 서비스를 찾을 수 없습니다! 카메라 노드 상태를 확인하세요.')
            return

        self.is_resetting = True
        request = Empty.Request()
        
        # 비동기 호출로 노드 멈춤 방지
        future = self.reset_client.call_async(request)
        future.add_done_callback(self.reset_done_callback)

    def reset_done_callback(self, future):
        """리셋 서비스 호출 완료 후 실행되는 콜백"""
        try:
            future.result()
            self.get_logger().info('✅ 하드웨어 리셋 명령을 성공적으로 보냈습니다. 복구를 기다립니다.')
        except Exception as e:
            self.get_logger().error(f'❌ 리셋 서비스 호출 실패: {e}')

        # 리셋 후 다시 데이터 수신을 기다리기 위해 시간 초기화
        self.last_msg_time = self.get_clock().now()
        self.is_resetting = False

    def imu_callback(self, msg):
        """IMU 데이터를 받아 TF 발행 (기존 로직 유지)"""
        # 데이터 유효성 검사 (0,0,0,0 체크)
        if (msg.orientation.x == 0.0 and msg.orientation.y == 0.0 and
            msg.orientation.z == 0.0 and msg.orientation.w == 0.0):
            self.get_logger().warn("빈(0,0,0,0) 데이터 수신 중...", throttle_duration_sec=1.0)
            return

        # 데이터 수신 상태 업데이트
        self.data_received_once = True
        self.last_msg_time = self.get_clock().now()

        # 다운샘플링 로직
        self.callback_count += 1
        if self.callback_count % self.skip_count != 0:
            return

        # 쿼터니언 계산 (원본 * 오프셋)
        q_orig = [msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w]
        q_raw = tf_transformations.quaternion_multiply(q_orig, self.q_offset)
        q_final = tf_transformations.unit_vector(q_raw)

        if q_final is None or np.any(np.isnan(q_final)):
            return

        # TF 메시지 생성 및 발행
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.rotation.x = q_final[0]
        t.transform.rotation.y = q_final[1]
        t.transform.rotation.z = q_final[2]
        t.transform.rotation.w = q_final[3]

        self.br.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = ImuTFBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()