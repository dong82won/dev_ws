import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from math import pow, atan2, sqrt, pi

def euler_from_quaternion(x, y, z, w):
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    return atan2(t3, t4)

class WaypointFollower(Node):
    def __init__(self):
        super().__init__('waypoint_follower')

        # ==========================================
        # ★★★ [튜닝 포인트] 속도 설정 영역 ★★★
        # ==========================================

        # 1. 최대 속도 제한 (Safety Limit)
        # 너무 빠르면 박스가 뒤집어질 수 있습니다.
        self.MAX_LIN_VEL = 0.5  # 최대 전진 속도 (m/s)
        self.MAX_ANG_VEL = 0.5  # 최대 회전 속도 (rad/s)

        # 2. 반응성 (Gain / P-Control)
        # 값이 클수록 목표에 빨리 도달하지만, 덜컹거리거나 오버슈트가 발생할 수 있습니다.
        self.LIN_GAIN = 0.5     # 전진 가속도 (거리 비례)
        self.ANG_GAIN = 1.5     # 회전 민감도 (각도 비례)

        # 3. 제자리 회전 임계값 (Threshold)
        # 목표 각도와 이 값 이상 차이나면 전진을 멈추고 회전만 합니다.
        # 값이 작을수록 정확히 돌고 출발하고(Tank Turn), 크면 부드럽게 곡선을 그리며 갑니다.
        self.TURN_THRESHOLD = 0.5 # 라디안 (약 30도)

        # ==========================================

        self.waypoints = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 0.0)]
        self.current_wp_index = 0

        self.cmd_pub = self.create_publisher(Twist, '/box_cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/box_odom', self.odom_callback, 10)
        self.timer = self.create_timer(0.1, self.control_loop)

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0 

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        rot = msg.pose.pose.orientation
        self.yaw = euler_from_quaternion(rot.x, rot.y, rot.z, rot.w)

    def control_loop(self):
        if self.current_wp_index >= len(self.waypoints):
            print("도착 완료.")
            self.stop_robot()
            return

        target_x, target_y = self.waypoints[self.current_wp_index]
        distance = sqrt(pow(target_x - self.x, 2) + pow(target_y - self.y, 2))
        
        if distance < 0.1:
            print(f"WP {self.current_wp_index} 도착. 이동 중...")
            self.current_wp_index = (self.current_wp_index + 1) % len(self.waypoints)
            return

        target_angle = atan2(target_y - self.y, target_x - self.x)
        angle_diff = target_angle - self.yaw

        if angle_diff > pi:
            angle_diff -= 2 * pi
        elif angle_diff < -pi:
            angle_diff += 2 * pi

        twist = Twist()

        # [1] 회전 속도 계산 (변수 적용)
        target_ang_speed = angle_diff * self.ANG_GAIN
        
        # 클램핑 (최대 속도 제한)
        if target_ang_speed > self.MAX_ANG_VEL:
            target_ang_speed = self.MAX_ANG_VEL
        elif target_ang_speed < -self.MAX_ANG_VEL:
            target_ang_speed = -self.MAX_ANG_VEL
            
        twist.angular.z = target_ang_speed

        # [2] 전진 속도 계산 (변수 적용)
        # 각도 오차가 임계값보다 크면 전진 금지 (제자리 회전)
        if abs(angle_diff) > self.TURN_THRESHOLD:
            twist.linear.x = 0.0
        else:
            # 거리 비례 속도 제어
            target_lin_speed = distance * self.LIN_GAIN
            
            # 클램핑
            if target_lin_speed > self.MAX_LIN_VEL:
                target_lin_speed = self.MAX_LIN_VEL
            
            twist.linear.x = target_lin_speed

        self.cmd_pub.publish(twist)
        print(f"거리: {distance:.2f} | 각도오차: {angle_diff:.2f}")

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

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