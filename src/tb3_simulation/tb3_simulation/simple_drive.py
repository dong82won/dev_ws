import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

# 간단하게 2초간 전진했다가 멈추는 코드
class SimpleDrive(Node):
    def __init__(self):
        super().__init__('simple_drive_node')
        # ★ 중요: 아까 모델에서 설정한 토픽 이름 '/box_cmd_vel' 확인
        self.publisher_ = self.create_publisher(Twist, '/box_cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.count = 0

    def timer_callback(self):
        msg = Twist()

        # 0.1초 * 30회 = 3초 동안 전진
        if self.count < 30:
            msg.linear.x = 0.5  # 앞으로 가라!
            print(f"전진 중... {self.count}")
        else:
            msg.linear.x = 0.0  # 멈춰라!
            print("정지!")
        self.publisher_.publish(msg)
        self.count += 1

def main(args=None):
    rclpy.init(args=args)
    node = SimpleDrive()
    # 5초 정도만 동작하고 종료
    start_time = time.time()
    while time.time() - start_time < 5:
        rclpy.spin_once(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()