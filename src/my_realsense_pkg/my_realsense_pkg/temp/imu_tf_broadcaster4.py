import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import math

class ImuTFBroadcaster(Node):
    def __init__(self):
        super().__init__('imu_tf_broadcaster')
        self.br = TransformBroadcaster(self)
        self.subscription = self.create_subscription(Imu, '/imu/filtered', self.imu_callback, 10)

        # 1. 센서 -> 로봇 뼈대 보정 (질문자님이 성공하신 값)
        # [x 옆, y 아래, z 정면] -> [x 앞, y 왼쪽, z 위]
        self.q_sensor_to_base = [0.5, -0.5, 0.5, 0.5]

        # 2. Odom(세계) -> IMU 필터(세계) 보정
        # 필터의 북쪽(North) 기준을 로봇의 정면(Odom X)으로 90도 회전시킵니다.
        # [x, y, z, w] -> Z축 기준 90도 회전값
        self.q_world_fix = [0.0, 0.0, 0.7071, 0.7071]
 


    # 두 쿼터니언을 곱하여 회전을 합치는 수학 함수
    def quaternion_multiply(self, q1, q2):
        x1, y1, z1, w1 = q1[0], q1[1], q1[2], q1[3]
        x2, y2, z2, w2 = q2[0], q2[1], q2[2], q2[3]
        return [
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
            w1*w2 - x1*x2 - y1*y2 - z1*z2
        ]

    def imu_callback(self, msg):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'        # 기준이 되는 세계
        t.child_frame_id = 'base_link'    # 회전시킬 로봇의 뿌리

        # 1. 필터에서 나온 IMU 원본 회전 (광학 좌표계 기준)
        q_orig = [msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w]
        
        # 회전 합성 공식: (세계 보정) * (원본 데이터) * (센서 보정)
        # 1. 먼저 필터의 세계관을 odom에 맞게 90도 돌립니다.
        combined_q = self.quaternion_multiply(self.q_world_fix, q_orig)
        
        # 2. 그 다음, 결과값을 로봇 뼈대(base_link) 좌표계로 변환합니다.
        q_final = self.quaternion_multiply(combined_q, self.q_sensor_to_base)

        # 4. TF에 최종 값 적용
        t.transform.rotation.x = q_final[0]
        t.transform.rotation.y = q_final[1]
        t.transform.rotation.z = q_final[2]
        t.transform.rotation.w = q_final[3]
        
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0

        self.br.sendTransform(t)

def main():
    rclpy.init()
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