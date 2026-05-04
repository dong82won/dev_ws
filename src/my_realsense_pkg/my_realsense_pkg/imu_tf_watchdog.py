import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import tf_transformations
import numpy as np
import math

class ImuTFBroadcaster(Node):
    def __init__(self):
        super().__init__('imu_tf_watchdog')

        # RealSense URDF(Roll -90, Yaw -90)를 정확히 원상복구(Inverse)시키는 마법의 쿼터니언
        # Optical Frame(Z정면, Y아래) -> Base Link(X정면, Z위) 로 완벽히 변환합니다.
        # 1. 오프셋 쿼터니언 (광학 -> 로봇 좌표계)
        self.declare_parameter('q_offset', [0.5, -0.5, 0.5, 0.5])
        self.q_offset = self.get_parameter('q_offset').get_parameter_value().double_array_value
        # self.q_offset = [0.5, -0.5, 0.5, 0.5]

        # 데이터 수신 여부 확인을 위한 변수
        self.last_msg_time = self.get_clock().now()
        self.data_received_once = False

        # 2. 다운샘플링을 위한 변수
        # 예: IMU가 200Hz로 들어오고 50Hz로 내보내고 싶다면 skip_count = 4
        self.callback_count = 0
        self.skip_count = 4  # 4번마다 1번씩 실행 (200Hz -> 50Hz)


        self.br = TransformBroadcaster(self)
        self.subscription = self.create_subscription(Imu, '/imu/filtered', self.imu_callback, 10)


        # 3. 데이터 수신 검증을 위한 타이머 (1초마다 체크)
        self.health_check_timer = self.create_timer(1.0, self.check_data_health)
        self.get_logger().info(f'최적화된 IMU TF Broadcaster 시작 (다운샘플링: 1/{self.skip_count})')

    def check_data_health(self):
        """데이터가 정상적으로 들어오고 있는지 검사하는 함수"""
        now = self.get_clock().now()
        elapsed_time = (now - self.last_msg_time).nanoseconds / 1e9 # 초 단위 계산

        if not self.data_received_once:
            # self.get_logger().warn('아직 IMU 데이터를 단 한 번도 받지 못했습니다. 토픽 연결을 확인하세요!', once=False)
            self.get_logger().warn('데이터 수신 대기 중...')
        elif elapsed_time > 2.0: # 2초 이상 데이터가 안 들어올 경우
            # self.get_logger().error(f'IMU 데이터 흐름이 끊겼습니다! (마지막 수신으로부터 {elapsed_time:.1f}초 경과)')
            self.get_logger().error(f'데이터 흐름 중단! ({elapsed_time:.1f}초 경과)')
    
    # 두 쿼터니언을 곱하여 회전을 합치는 수학 함수
    def quaternion_multiply(self, q1, q2):
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2
        return [
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
            w1*w2 - x1*x2 - y1*y2 - z1*z2
        ]

    def normalize_quaternion(self, q):
        """
        쿼터니언의 크기를 1로 만드는 정규화 함수
        :param q: [x, y, z, w] 리스트
        :return: 정규화된 리스트 또는 입력 리스트 그대로 반환
        """
        # 1. 크기(Norm) 계산
        norm = sum(i**2 for i in q)**0.5

        # 2. 예외 처리: 분모가 0이거나 너무 작은 경우 (invalid quaternion)
        # RViz에서 본 (0,0,0,0) 같은 상황을 방지합니다.
        if norm < 1e-6:
            # 여기에 경고 로그 추가: 데이터가 깨졌음을 알림
            self.get_logger().warn("IMU 데이터의 크기가 너무 작아 정규화할 수 없습니다. (Identity 반환)")
            # 계산이 불가능하므로 기본값(회전 없음)을 반환하거나 기존 값을 유지합니다.
            return [0.0, 0.0, 0.0, 1.0]

        # 3. 각 요소를 norm으로 나누어 반환
        return [i/norm for i in q]


    def imu_callback(self, msg):

        # # 데이터 수신 상태 업데이트
        # if not self.data_received_once:
        #     self.get_logger().info('첫 번째 IMU 데이터를 성공적으로 수신했습니다.')
        #     self.data_received_once = True
        # self.last_msg_time = self.get_clock().now()


        # 1. 입력받은 쿼터니언이 유효한지 확인 (모두 0이면 무시)
        # 데이터 유효성 검사 (0,0,0,0 체크)
        if (msg.orientation.x == 0.0 and msg.orientation.y == 0.0 and
            msg.orientation.z == 0.0 and msg.orientation.w == 0.0):
            # self.get_logger().warn("Invalid quaternion received: all zeros") # 너무 자주 뜨면 주석 처리
            # 0.5초마다 한 번씩만 출력하도록 설정 (너무 많이 나오면 터미널이 어지러우므로)
            self.get_logger().warn("센서로부터 빈(0,0,0,0) 데이터가 수신되고 있습니다.", throttle_duration_sec=0.5)
            return

        self.data_received_once = True
        self.last_msg_time = self.get_clock().now()

        # [CPU 최적화] 다운샘플링 로직
        self.callback_count += 1
        if self.callback_count % self.skip_count != 0:
            return



        # 1. 필터에서 나온 IMU 원본 회전 (광학 좌표계 기준)
        # [성능 최적화] 직접 구현한 함수 대신 tf_transformations 사용
        q_orig = [msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w]

        # # 2. 광학 좌표계를 로봇 좌표계로 보정 (원본 * 오프셋)
        # q_raw = self.quaternion_multiply(q_orig, self.q_offset)
        # # 3. 계산된 쿼터니언을 정규화하여 RViz에서 올바르게 표시되도록 합니다.
        # q_final = self.normalize_quaternion(q_raw)

        # 쿼터니언 곱셈 (회전 합성)
        q_raw = tf_transformations.quaternion_multiply(q_orig, self.q_offset)
        # 쿼터니언 정규화
        q_final = tf_transformations.unit_vector(q_raw)

        # [수정된 방어 로직]
        # 1. q_final이 None인지 확인
        # 2. q_final 안에 NaN(결측치)이 포함되어 있는지 확인 (0으로 나누기 방지)
        if q_final is None or np.any(np.isnan(q_final)):
            self.get_logger().warn("계산된 쿼터니언이 유효하지 않습니다(NaN). 데이터를 건너뜁니다.")
            return

        # 4. TF 메시지 생성
        t = TransformStamped()
        # t.header.stamp = self.get_clock().now().to_msg()
        # [수정 부분] 시스템 시간이 아닌, IMU 센서가 데이터를 생성한 시간을 그대로 사용합니다.
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'        # 기준이 되는 세계
        t.child_frame_id = 'base_link'    # 회전시킬 로봇의 뿌리


        # 4. TF에 최종 값 적용
        t.transform.rotation.x = q_final[0]
        t.transform.rotation.y = q_final[1]
        t.transform.rotation.z = q_final[2]
        t.transform.rotation.w = q_final[3]

        # t.transform.translation.x = 0.0
        # t.transform.translation.y = 0.0
        # t.transform.translation.z = 0.0

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