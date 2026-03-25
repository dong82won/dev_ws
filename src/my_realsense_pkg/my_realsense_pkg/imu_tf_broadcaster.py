import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class ImuTFBroadcaster(Node):
    def __init__(self):
        super().__init__('imu_tf_broadcaster')
        self.br = TransformBroadcaster(self)
        self.subscription = self.create_subscription(Imu, '/imu/filtered', self.imu_callback, 10)

    def imu_callback(self, msg):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'        # 기준이 되는 세계
        t.child_frame_id = 'base_link'    # 회전시킬 로봇의 뿌리

        # IMU로부터 받은 쿼터니언(회전) 값 그대로 적용
        t.transform.rotation = msg.orientation

        # 위치(xyz)는 고정 (원한다면 수정 가능)
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0

        self.br.sendTransform(t)

def main():
    rclpy.init()
    node = ImuTFBroadcaster()
    rclpy.spin(node)
    rclpy.shutdown()