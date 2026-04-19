import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

# LB (buttons[4])
# RB (buttons[5])
# LT (buttons[6])
# RT (buttons[7])

class CustomJoyTeleop(Node):
    def __init__(self):
        super().__init__('custom_joy_teleop')

        # cmd_vel 퍼블리셔 및 joy 서브스크라이버 생성
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(Joy, 'joy', self.joy_callback, 10)

        # --- 초기 속도 및 조절 단위 설정 ---
        self.declare_parameter('initial_max_linear_vel', 0.1)  # 초기 선속도 최대치 (m/s)
        self.declare_parameter('initial_max_angular_vel', 0.5) # 초기 각속도 최대치 (rad/s)
        self.declare_parameter('linear_step', 0.2)             # Y, A 버튼 한 번 누를 때 변하는 선속도 양
        self.declare_parameter('angular_step',0.2)             # X, B 버튼 한 번 누를 때 변하는 각속도 양

        # 필터 계수 (0.0 ~ 1.0). 값이 작을수록 가감속이 부드럽게(천천히) 일어남
        self.declare_parameter('alpha_linear',0.7)
        self.declare_parameter('alpha_angular',0.7)
        # --- 조이스틱 데드존(Deadzone) 설정 ---
        # 5% 미만의 입력값은 노이즈(물리적 찌꺼기)로 간주하고 0.0으로 무시
        self.declare_parameter('deadzone',0.05)

        self.max_linear_vel = self.get_parameter('initial_max_linear_vel').get_parameter_value().double_value
        self.max_angular_vel = self.get_parameter('initial_max_angular_vel').get_parameter_value().double_value
        self.linear_step = self.get_parameter('linear_step').get_parameter_value().double_value
        self.angular_step = self.get_parameter('angular_step').get_parameter_value().double_value
        self.alpha_linear = self.get_parameter('alpha_linear').get_parameter_value().double_value
        self.alpha_angular = self.get_parameter('alpha_angular').get_parameter_value().double_value
        self.deadzone = self.get_parameter('deadzone').get_parameter_value().double_value

        # 버튼 중복 눌림 방지용 이전 상태 저장 리스트
        self.last_buttons = [0] * 15

        # --- 가속도 필터(Low-pass Filter)용 변수 ---
        self.target_linear_vel = 0.0    # 조이스틱이 지시하는 '목표 선속도'
        self.target_angular_vel = 0.0   # 조이스틱이 지시하는 '목표 각속도'
        self.current_linear_vel = 0.0   # 로봇에게 실제 전송할 '현재 선속도'
        self.current_angular_vel = 0.0  # 로봇에게 실제 전송할 '현재 각속도'


        # --- 타임아웃(안전) 설정 ---
        self.last_joy_time = self.get_clock().now() # 마지막으로 메시지를 받은 시간 저장
        self.timeout_sec = 0.5                      # 0.5초 이상 신호가 없으면 끊긴 것으로 간주
        self.is_timeout = False                     # 현재 타임아웃 상태인지 확인하는 플래그

        # 0.05초 (20Hz)마다 통신 상태를 확인하는 타이머 생성
        # 수정 후: 50Hz (0.02초)로 변경하여 더 부드러운 명령 전달
        self.timer = self.create_timer(0.02, self.control_loop_callback)

        self.get_logger().info('Custom F710 Teleop Node Started.')
        self.get_logger().info('Teleop Node Started with Low-Pass Filter.')
        self.get_logger().info('Hold [LB] button to enable movement.')
        self.get_logger().info(f'Current Max Linear Vel: {self.max_linear_vel} m/s')
        self.get_logger().info(f'Current Max Angular Vel: {self.max_angular_vel} rad/s')


    def joy_callback(self, msg):
        # 1. 메시지가 들어오면 마지막 수신 시간 업데이트 및 타임아웃 해제
        self.last_joy_time = self.get_clock().now()

        if self.is_timeout:
            self.get_logger().info('Joystick signal restored.')
            self.is_timeout = False

        # --- 1. 속도 조절 로직 (버튼 상태 변화 감지) ---
        # Y (buttons[3]): 선속도 증가
        if msg.buttons[3] == 1 and self.last_buttons[3] == 0:
            self.max_linear_vel += self.linear_step
            self.get_logger().info(f'Linear Speed UP: {self.max_linear_vel:.2f} m/s')
        # A (buttons[1]): 선속도 감소 (수정됨: 중복 빼기 제거)
        elif msg.buttons[1] == 1 and self.last_buttons[1] == 0:
            self.max_linear_vel = max(0.0, self.max_linear_vel - self.linear_step)
            self.get_logger().info(f'Linear Speed DOWN: {self.max_linear_vel:.2f} m/s')

        # B (buttons[2]): 각속도 증가
        if msg.buttons[2] == 1 and self.last_buttons[2] == 0:
            self.max_angular_vel += self.angular_step
            self.get_logger().info(f'Angular Speed UP: {self.max_angular_vel:.2f} rad/s')

        # X (buttons[0]): 각속도 감소 (수정됨: 중복 빼기 제거)
        elif msg.buttons[0] == 1 and self.last_buttons[0] == 0:
            self.max_angular_vel = max(0.0, self.max_angular_vel - self.angular_step)
            self.get_logger().info(f'Angular Speed DOWN: {self.max_angular_vel:.2f} rad/s')

        # 다음 콜백을 위해 현재 버튼 상태 저장
        self.last_buttons = list(msg.buttons)

        # --- 2. 이동 명령 생성 (LB 버튼 Deadman Switch 및 Deadzone Rescaling 적용) ---
        # 로컬 twist 변수 대신 target_vel 변수를 직접 업데이트합니다.
        # LB 버튼: msg.buttons[4]
        # 왼쪽 스틱 위/아래: msg.axes[5]
        # 오른쪽 스틱 좌/우: msg.axes[2]
        # 최우선 순위: RB 버튼 (E-Stop)
        if msg.buttons[5] == 1:
            # 목표 속도뿐만 아니라 '현재 속도(current_vel)'까지 즉시 0으로 강제 초기화하여 필터를 무시함
            self.target_linear_vel = 0.0
            self.target_angular_vel = 0.0
            self.current_linear_vel = 0.0
            self.current_angular_vel = 0.0
            self.get_logger().warn('E-STOP ACTIVATED! Hard Braking!', throttle_duration_sec=1.0)
        elif msg.buttons[4] == 1:
            # 헬퍼 함수를 통해 데드존 적용 및 부드러운 스케일링(Rescaling)이 완료된 축 값 가져오기
            clean_linear = self.apply_deadzone_and_rescale(msg.axes[1])
            clean_angular = self.apply_deadzone_and_rescale(msg.axes[2])

            # 재조정된 값으로 목표 속도 업데이트
            self.target_linear_vel = clean_linear * self.max_linear_vel
            self.target_angular_vel = clean_angular * self.max_angular_vel
        else:
            # LB 버튼에서 손을 떼면 목표 속도를 0으로 설정하여 필터를 통해 부드럽게 감속
            self.target_linear_vel = 0.0
            self.target_angular_vel = 0.0
            self.current_linear_vel = 0.0   # 추가: 즉시 정지
            self.current_angular_vel = 0.0  # 추가: 즉시 정지

    def apply_deadzone_and_rescale(self, raw_value):
        """
        입력값에 데드존을 적용하고, 데드존 이후의 값을 0.0 ~ 1.0(또는 -1.0)으로 부드럽게 재조정합니다.
        """
        if abs(raw_value) < self.deadzone:
            return 0.0
        # 부호 추출 (+1.0 또는 -1.0)
        sign = 1.0 if raw_value > 0 else -1.0
        # 데드존(0.05) ~ 최대 스틱(1.0) 구간을 -> 0.0 ~ 1.0으로 스케일링
        rescaled_value = sign * (abs(raw_value) - self.deadzone) / (1.0 - self.deadzone)
        return rescaled_value

    def control_loop_callback(self):
        # 1. 타임아웃 검사
        # 현재 시간과 마지막으로 조이스틱 메시지를 받은 시간의 차이를 초 단위로 계산
        elapsed_time = (self.get_clock().now() - self.last_joy_time).nanoseconds / 1e9
        # 설정된 타임아웃(0.5초)을 초과했다면 로봇 정지 명령 발행
        if elapsed_time > self.timeout_sec:
            if not self.is_timeout:
                self.get_logger().warn('Joystick timeout! Stopping the robot.')
                self.is_timeout = True
            # 통신이 끊기면 목표 속도를 0으로 만들어 자연스럽게 감속 정지하도록 유도
            self.target_linear_vel = 0.0
            self.target_angular_vel = 0.0


        # # 2. Low-pass Filter 적용 (수식: 현재 = 현재 + (목표 - 현재) * alpha)
        # self.current_linear_vel += (self.target_linear_vel - self.current_linear_vel) * self.alpha_linear
        # self.current_angular_vel += (self.target_angular_vel - self.current_angular_vel) * self.alpha_angular

        # # 3. 미세한 속도 찌꺼기 제거 (목표가 0일 때 무한히 0에 수렴만 하는 것을 방지)
        # if abs(self.current_linear_vel) < 0.001:
        #     self.current_linear_vel = 0.0
        # if abs(self.current_angular_vel) < 0.001:
        #     self.current_angular_vel = 0.0

        # 2. Low-pass Filter 적용
        # 목표값과 현재값의 차이가 아주 작으면 필터를 타지 않고 바로 목표값으로 고정 (진동 방지)
        diff_linear = self.target_linear_vel - self.current_linear_vel
        diff_angular = self.target_angular_vel - self.current_angular_vel

        if abs(diff_linear) < 0.005:
            self.current_linear_vel = self.target_linear_vel
        else:
            self.current_linear_vel += diff_linear * self.alpha_linear

        if abs(diff_angular) < 0.005:
            self.current_angular_vel = self.target_angular_vel
        else:
            self.current_angular_vel += diff_angular * self.alpha_angular



        # 4. Twist 메시지 발행
        twist = Twist()
        twist.linear.x = self.current_linear_vel
        twist.angular.z = self.current_angular_vel
        self.publisher_.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = CustomJoyTeleop()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Teleop Node Stopped.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

# if __name__ == '__main__':
#     main()