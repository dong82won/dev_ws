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

        # ★ 여기에 보정할 각도(도 단위, Degrees)를 입력하세요.
        # 카메라가 세워져 있다면 Pitch나 Roll을 90도 또는 -90도로 변경하며 맞춥니다.
        self.roll_offset_deg = 90.0
        self.pitch_offset_deg = 0.0  # 예시: 고개를 숙이도록 -90도 보정
        self.yaw_offset_deg = 90.0

    # 오일러 각도(Degree)를 쿼터니언으로 변환하는 수학 함수
    def get_quaternion_from_euler(self, roll, pitch, yaw):
        roll = math.radians(roll)
        pitch = math.radians(pitch)
        yaw = math.radians(yaw)
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        return [qx, qy, qz, qw]

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

        # 1. IMU에서 온 원본 회전값
        q_orig = [msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w]
        
        # 2. 우리가 설정한 보정 각도(Offset)
        q_rot = self.get_quaternion_from_euler(self.roll_offset_deg, self.pitch_offset_deg, self.yaw_offset_deg)
        
        # 3. 원본 회전에 보정 각도를 곱하여 최종 회전값 계산
        q_final = self.quaternion_multiply(q_orig, q_rot)

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
    rclpy.spin(node)
    rclpy.shutdown()