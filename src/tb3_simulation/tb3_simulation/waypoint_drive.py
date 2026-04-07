import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from math import pow, atan2, sqrt, asin

# 쿼터니언(4차원)을 오일러(각도)로 변환하는 함수
def euler_from_quaternion(x, y, z, w):
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    return atan2(t3, t4)

class WaypointFollower(Node):
    def __init__(self):
        super().__init__('waypoint_follower')
        
        # 1. 설정: 목표 웨이포인트 리스트 (x, y)
        self.waypoints = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 0.0)]
        self.current_wp_index = 0
        
        # 2. 통신 설정
        # 명령 보내기
        self.cmd_pub = self.create_publisher(Twist, '/box_cmd_vel', 10)
        # 내 위치 듣기 (필수!)
        self.odom_sub = self.create_subscription(Odometry, '/box_odom', self.odom_callback, 10)
        
        # 3. 제어 주기 (0.1초마다 계산)
        self.timer = self.create_timer(0.1, self.control_loop)
        
        # 로봇 상태 변수
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0 # 로봇이 바라보는 방향 (헤딩)

    # 오도메트리에서 현재 위치 업데이트
    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        # 쿼터니언 -> 오일러 변환 (방향 알아내기)
        rot = msg.pose.pose.orientation
        self.yaw = euler_from_quaternion(rot.x, rot.y, rot.z, rot.w)

    def control_loop(self):
        if self.current_wp_index >= len(self.waypoints):
            print("모든 웨이포인트 도착 완료! 정지합니다.")
            self.stop_robot()
            return

        # 현재 목표 지점 가져오기
        target_x, target_y = self.waypoints[self.current_wp_index]
        
        # 1. 거리 오차 계산 (피타고라스 정리)
        distance = sqrt(pow(target_x - self.x, 2) + pow(target_y - self.y, 2))
        
        # 2. 목표 도착 확인 (오차 0.1m 이내면 도착으로 간주)
        if distance < 0.1:
            print(f"웨이포인트 {self.current_wp_index} 도착! 다음으로 이동...")
            self.current_wp_index = (self.current_wp_index + 1) % len(self.waypoints) # 무한 반복
            return

        # 3. 각도 오차 계산 (atan2로 목표 지점의 각도 구하기)
        target_angle = atan2(target_y - self.y, target_x - self.x)
        angle_diff = target_angle - self.yaw

        # 각도 정규화 (-PI ~ PI 사이로 맞춤)
        if angle_diff > 3.14159:
            angle_diff -= 2 * 3.14159
        elif angle_diff < -3.14159:
            angle_diff += 2 * 3.14159

        # 4. 주행 명령 생성 (P-Control: 오차에 비례해서 속도 조절)
        twist = Twist()

        # [수정] 회전 속도(Angular Velocity) 제한 걸기
        # 기존: twist.angular.z = angle_diff * 2.0 (오차가 180도면 속도가 6.28로 너무 빠름!)        
        
        max_angular_speed = 0.5  # 최대 회전 속도를 0.5 rad/s로 제한 (천천히 돌기)
        target_angular_speed = angle_diff * 1.5

        # 속도 클램핑 (최대값보다 크면 잘라냄)
        if target_angular_speed > max_angular_speed:
            target_angular_speed = max_angular_speed
        elif target_angular_speed < -max_angular_speed:
            target_angular_speed = -max_angular_speed

        twist.angular.z = target_angular_speed

        # # 각도 오차가 크면 제자리 회전, 작으면 전진
        # if abs(angle_diff) > 0.1:
        #     twist.linear.x = 0.0
        #     twist.angular.z = angle_diff * 1.5 # 회전 속도 (상수 1.5는 튜닝 값)
        # else:
        #     twist.linear.x = 0.5 * distance # 거리가 멀면 빨리, 가까우면 천천히
        #     if twist.linear.x > 0.5: twist.linear.x = 0.5 # 최대 속도 제한
        #     twist.angular.z = angle_diff * 2.0 # 이동하면서 미세 조향

        # [수정] 전진할 때도 각도 오차가 크면 아예 멈추고 돌기만 하게 설정
        if abs(angle_diff) > 0.5: # 0.5라디안(약 30도) 이상 틀어져 있으면
            twist.linear.x = 0.0  # 전진 금지 (제자리 회전)
        else:
            twist.linear.x = 0.5 * distance
            if twist.linear.x > 0.5: twist.linear.x = 0.5


        self.cmd_pub.publish(twist)
        print(f"목표: ({target_x}, {target_y}) | 거리: {distance:.2f}m | 각도오차: {angle_diff:.2f}")

    def stop_robot(self):
        twist = Twist()
        self.cmd_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = WaypointFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.stop_robot()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()