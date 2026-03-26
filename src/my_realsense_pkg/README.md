질문해주신 내용을 보면 `robot_state_publisher`를 우선 제외한다고 하셨지만, 첨부해주신 URDF 파일들의 구조를 보면 **이 세 가지 패키지는 톱니바퀴처럼 맞물려 돌아가야 가장 완벽한 TF 트리를 구성할 수 있습니다.** 첨부해주신 URDF 코드를 분석해 보면, RealSense 설계팀에서 아주 영리하게 파라미터를 통해 "누가 카메라 내부 TF를 발행할 것인가?"를 선택할 수 있도록 만들어 두었습니다. 이를 바탕으로 최적의 조합을 설명해 드릴게요.

---

### 1. 첨부된 URDF의 핵심: `use_nominal_extrinsics`

[cite_start]제공해주신 파일 중 최상위 역할을 하는 `test_d435i_camera.urdf.xacro`를 보면, 로봇의 중심인 `base_link`를 정의하고 그 위에 D435i 카메라를 부착하고 있습니다[cite: 15]. 
[cite_start]여기서 가장 주목해야 할 부분은 `use_nominal_extrinsics` 인자가 기본값 `false`로 설정되어 있다는 점입니다[cite: 15].

* [cite_start]**만약 이 값이 `true`라면:** `_d435i_imu_modules.urdf.xacro` 파일 내의 조건문이 작동하여, `_accel_frame`, `_gyro_frame` 등의 IMU 링크들이 생성됩니다[cite: 12]. [cite_start]또한 부모 링크와 이 자식 링크들을 연결하는 고정(fixed) 조인트들이 함께 생성됩니다[cite: 12, 13, 14].
* [cite_start]**기본값인 `false`를 유지한다면[cite: 15]:** 해당 조건문이 무시되므로, `robot_state_publisher`는 카메라 내부의 IMU 프레임이나 TF 구조를 전혀 생성하지 않습니다.


질문하신 `use_nominal_extrinsics` 파라미터는 RealSense 카메라의 TF(좌표계 변환) 트리를 구성할 때 **"설계도상의 이상적인 수치(Nominal)를 사용할 것인가, 아니면 실제 기기의 캘리브레이션 수치를 사용할 것인가"**를 결정하는 아주 중요한 옵션입니다. 

질문하신 내용에 대한 정확한 답변은 다음과 같습니다.

### 1. `use_nominal_extrinsics`의 기본값은 `false`인가요?
**네, 맞습니다.** `realsense-ros` 패키지의 URDF(`_d435.urdf.xacro` 등) 파일 내부를 보면 해당 인자의 기본값(default)은 `false`로 설정되어 있습니다.

### 2. `use_nominal_extrinsics` 값이 `true`이면 어떻게 되나요?
값이 `true`가 되면 **URDF 파일 안에 하드코딩되어 있는 '공장 설계 도면상의 기준 수치(Nominal values)'를 바탕으로 `robot_state_publisher`가 카메라 내부의 모든 정적 TF(Static TF)를 직접 발행**하게 됩니다.

구체적으로 다음과 같은 차이가 발생합니다.

* **`true`일 때 일어나는 일 (주로 시뮬레이션용):**
    * URDF가 `camera_link`를 기준으로 `camera_color_frame`, `camera_depth_frame`, `camera_imu_optical_frame` 등의 세부 렌즈/센서 위치 TF를 모두 찍어냅니다.
    * **언제 사용하나요?** Gazebo와 같은 **시뮬레이션 환경**에서 주로 사용합니다. 가상 환경의 카메라는 실제 하드웨어가 없어서 내부 펌웨어에서 캘리브레이션 값을 읽어올 수 없으므로, URDF가 제공하는 가짜(Nominal) TF라도 있어야 시스템이 돌아가기 때문입니다.
* **`false`일 때 일어나는 일 (실제 카메라용 - 권장):**
    * URDF는 카메라의 뼈대(`base_link` $\rightarrow$ `camera_link`) 정도만 만들어두고, 렌즈 간의 세부적인 내부 TF 발행은 중단합니다.
    * 대신 **`realsense2_camera_node` (실제 카메라 드라이버 노드)가 하드웨어 센서에서 직접 읽어온 '초정밀 공장 캘리브레이션 값'을 바탕으로 실제 카메라 구조에 완벽히 들어맞는 TF를 실시간으로 발행**합니다.

---

**⚠️ 주의사항 (TF 충돌):**
만약 실제 카메라 하드웨어를 연결해 놓고 런치 파일에서 이 값을 `true`로 줘버리면, **URDF가 발행하는 가짜 정적 TF**와 **RealSense 노드가 발행하는 진짜 캘리브레이션 TF**가 동시에 같은 토픽 이름으로 쏟아져 나오게 됩니다. 결과적으로 하나의 자식 프레임이 두 개의 부모를 갖게 되는 **TF 충돌(TF Tree 붕괴)**이 발생하여 RViz에서 카메라 모델이 깨지거나 에러가 나게 됩니다.

따라서 실제 로봇/카메라를 구동하실 때는 질문자님께서 작성하신 대로 `use_nominal_extrinsics:=false` 상태를 유지하는 것이 완벽한 정답입니다!

궁금증이 해결되셨나요? 더 깊이 알고 싶은 ROS 파라미터가 있다면 편하게 질문해 주세요.



### 2. 최적의 TF 역할 분담 (왜 `false` 상태가 최적인가?)

[cite_start]결론적으로 **제공해주신 URDF의 기본값(`false`)을 그대로 유지하고, 실제 기기 값을 읽어오는 카메라 노드가 내부 TF를 쏘게 하는 것이 최적의 조합**입니다[cite: 15]. 

최적의 역할 분담은 다음과 같습니다.

* [cite_start]**`robot_state_publisher` (URDF 기반):** `test_d435i_camera.urdf.xacro`를 읽어 로봇의 중심(`base_link`)부터 카메라의 기준점까지만을 연결하는 뼈대 TF를 발행합니다[cite: 15]. 카메라 내부의 렌즈나 IMU 위치 등 미세한 영역은 관여하지 않고 비워둡니다.
* **`realsense2_camera`:** 카메라 노드가 켜지면, 기기 펌웨어에 저장된 **실제 공장 교정값(Factory Calibration)**을 읽어옵니다. URDF에 적힌 딱딱한 설계도 상의 수치보다 실제 물리적 수치가 훨씬 정확하기 때문에, 이 노드가 `camera_link` 하위의 IMU 광학 프레임(Optical frames)들로 이어지는 TF를 직접 발행하게 두는 것이 정확도를 높이는 핵심입니다.
* **`imu_filter_madgwick`:** 이전 설명과 동일합니다. 이 패키지는 `realsense2_camera`가 보내주는 센서 데이터를 받아 수학적으로 필터링만 수행해야 합니다. 기존의 잘 짜인 TF 트리를 망치지 않도록 절대 TF를 발행해서는 안 됩니다 (`publish_tf: false`).

---

### 3. 완성되는 최적의 단일 TF 트리 구조

위와 같이 역할을 분담하면, 충돌이나 떨림 현상 없이 물 흐르듯 이어지는 깔끔한 트리가 완성됩니다.

* `base_link` 
    * [cite_start]$\rightarrow$ `camera_link` (발행 주체: **`robot_state_publisher`** + 첨부하신 URDF [cite: 15])
        * $\rightarrow$ `camera_accel_optical_frame` / `camera_gyro_optical_frame` (발행 주체: **`realsense2_camera`**가 실제 기기 교정값을 바탕으로 생성)
* **[데이터 연산 전용]** 필터링된 방향 데이터 `/imu/data` 발행 (주체: **`imu_filter_madgwick`** / TF 트리에 개입하지 않음)

---

첨부해주신 URDF가 이미 훌륭하게 모듈화되어 있어서, 실행 시 파라미터만 잘 맞물려주면 완벽하게 구동될 것으로 보입니다. 
이 세 가지 노드(URDF 퍼블리셔, 카메라 노드, IMU 필터)를 한 번에 실행하면서 파라미터 충돌을 막아주는 통합 **ROS 2 Launch 파일 코드**를 작성해 드릴까요?

지금까지 논의한 최적의 구조를 바탕으로, 세 개의 패키지를 한 번에 실행하면서 충돌을 방지하는 **ROS 2 Python Launch 파일 (`camera_imu_bringup.launch.py`)** 예시를 작성해 드립니다.

이 코드는 `robot_state_publisher`가 뼈대를 잡고, `realsense2_camera`가 실제 기기 기반의 미세 TF와 합쳐진 IMU 데이터를 쏘며, `imu_filter_madgwick`이 조용히 데이터 연산만 수행하도록 모든 파라미터가 세팅되어 있습니다.

### ROS 2 Launch 파일 작성 (`camera_imu_bringup.launch.py`)

```python
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # 1. URDF 파일 경로 설정 
    # ★ 주의: 'my_robot_description' 부분을 실제 URDF가 있는 본인의 패키지 이름으로 변경하세요!
    urdf_file = PathJoinSubstitution([
        FindPackageShare('my_robot_description'), 
        'urdf',
        'test_d435i_camera.urdf.xacro'
    ])

    # xacro 명령어를 통해 URDF 파싱
    # use_nominal_extrinsics를 false로 주어 URDF가 가짜 IMU TF를 만들지 못하게 막습니다.
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        urdf_file,
        ' use_nominal_extrinsics:=false' 
    ])

    # 2. robot_state_publisher 노드
    # URDF를 읽어 base_link -> camera_link 까지의 뼈대 정적 TF를 발행합니다.
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}]
    )

    # 3. realsense2_camera 노드
    # 실제 기기 보정값을 읽어와 camera_link 하위의 렌즈 및 IMU TF를 완성하고 데이터를 쏩니다.
    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='camera',
        name='camera',
        output='screen',
        parameters=[{
            'enable_gyro': True,            # 자이로스코프 켜기
            'enable_accel': True,           # 가속도계 켜기
            'unite_imu_method': 2,          # 중요: accel과 gyro를 하나의 /camera/imu 토픽으로 합침 (2 = linear_interpolation)
            'enable_sync': True,            # 이미지와 IMU 데이터의 타임스탬프 동기화
            'publish_tf': True,             # 기본값이지만, 카메라 내부 TF를 쏘도록 확실히 활성화
        }]
    )

    # 4. imu_filter_madgwick 노드
    # RealSense의 Raw IMU를 받아 쿼터니언(방향)을 계산하되, TF는 절대 쏘지 않습니다.
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        output='screen',
        parameters=[{
            'use_mag': False,               # 필수: D435i에는 지자기 센서가 없으므로 끕니다.
            'publish_tf': False,            # 필수: 기존 TF 트리를 망치지 않도록 필터 자체의 TF 발행을 끕니다.
            'world_frame': 'enu'            # ROS 표준 좌표계(East-North-Up) 사용
        }],
        remappings=[
            # 필터가 RealSense의 합쳐진 IMU 토픽을 구독하도록 연결
            ('/imu/data_raw', '/camera/imu'), 
            # 필터링이 완료된(방향이 포함된) IMU 토픽의 출력 이름
            ('/imu/data', '/camera/imu/filtered') 
        ]
    )

    return LaunchDescription([
        rsp_node,
        realsense_node,
        imu_filter_node
    ])
```

---

### 실행 전 확인 사항

* **패키지 이름 수정:** 코드의 11번째 줄에 있는 `'my_robot_description'`을 현재 `test_d435i_camera.urdf.xacro` 파일이 위치한 패키지 이름으로 반드시 변경해 주세요.
* **빌드:** Launch 파일을 패키지의 `launch` 폴더에 넣고 `CMakeLists.txt` (C++) 또는 `setup.py` (Python)에 launch 폴더 설치 설정을 확인한 후 `colcon build`를 실행해 주세요.

이 런치 파일을 실행한 후, 터미널에서 `ros2 run tf2_tools view_frames` 명령어를 쳐보시면 `base_link`부터 카메라 내부 프레임까지 하나로 예쁘게 연결된 완벽한 단일 TF 트리를 PDF 형식으로 확인하실 수 있습니다. 

코드를 적용하시면서 혹시 의존성 에러나 토픽 이름 불일치 문제가 발생한다면 언제든 다시 질문해 주세요! 추가로 도와드릴 부분이 있을까요?



질문자님의 직관이 **100% 정확합니다!** "원래 로봇이 평지에 똑바로 놓여 있고 정면을 보고 있다면, `odom`과 `base_link`는 완벽하게 동일한 포즈(회전값 0)를 가져야 하는 것 아닌가?" 
$\rightarrow$ **네, 무조건 그래야 정상입니다.**

그런데 왜 각도를 넣어도 원하는 대로 예쁘게 정렬되지 않고 계속 꼬이는 걸까요? 그 이유는 **'오일러 각도(Roll, Pitch, Yaw)의 계산 순서(회전 순서)'**와 **'렌즈 좌표계의 복합적인 틀어짐'** 때문입니다. 

이 문제를 단번에 해결할 수 있는 가장 확실한 원리와 **수학적으로 완벽히 보정된 최종 파이썬 코드**를 제공해 드릴게요.

---

### 1. 왜 -90이나 90을 넣어도 마음대로 안 움직였을까요?

첨부해주신 URDF 파일(`_d435i_imu_modules.urdf.xacro`)을 보면, RealSense 설계팀이 IMU 센서를 카메라 뼈대에 붙일 때 다음과 같은 각도로 비틀어 붙여놓았습니다.
* `rpy = "-1.5707 0 -1.5707"` (즉, Roll -90도, Yaw -90도)

이 말은, IMU 센서 자체가 이미 X축으로 한 번 구르고, Z축으로 한 번 더 돌아가 있는 **'복합 회전'** 상태라는 뜻입니다. 

이것을 원상복구(Inverse) 시키려면 우리가 직관적으로 숫자 하나를 바꾸는 것으로는 해결하기 어렵습니다. (X축을 먼저 돌리냐, Z축을 먼저 돌리냐에 따라 결과가 완전히 달라지는 '짐벌 락' 현상 때문입니다.)

### 2. 해결책: URDF의 역회전(Inverse) 쿼터니언을 직접 곱하기

숫자를 찍어서 맞추는 대신, **URDF에 적힌 회전의 정확한 '반대(역변환)' 값을 쿼터니언으로 계산하여 코드에 고정**해버리면 `odom`과 `base_link`가 완벽하게 일치하게 됩니다.

기존의 `imu_tf_broadcaster.py` 코드를 아래의 **최종 버전**으로 완전히 덮어씌워 주세요. 오일러 각도를 계산하는 대신, RealSense 광학 좌표계를 로봇 좌표계로 완벽히 바꿔주는 고정된 수학적 역행렬 쿼터니언(`[0.5, -0.5, 0.5, 0.5]`)을 적용했습니다.

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class ImuTFBroadcaster(Node):
    def __init__(self):
        super().__init__('imu_tf_broadcaster')
        self.br = TransformBroadcaster(self)
        self.subscription = self.create_subscription(Imu, '/camera/imu/filtered', self.imu_callback, 10)

        # RealSense URDF(Roll -90, Yaw -90)를 정확히 원상복구(Inverse)시키는 마법의 쿼터니언
        # Optical Frame(Z정면, Y아래) -> Base Link(X정면, Z위) 로 완벽히 변환합니다.
        self.q_offset = [0.5, -0.5, 0.5, 0.5] # [x, y, z, w]

    # 두 쿼터니언을 곱하는 함수 (회전 합성)
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
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        # 1. 필터에서 나온 IMU 원본 회전 (광학 좌표계 기준)
        q_orig = [msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w]
        
        # 2. 광학 좌표계를 로봇 좌표계로 보정 (원본 * 오프셋)
        q_final = self.quaternion_multiply(q_orig, self.q_offset)

        # 3. 최종 TF 적용
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
```

---

### 3. 적용 후 기대되는 완벽한 결과

이 코드를 실행하시고 RViz에서 Fixed Frame을 **`odom`**으로 설정해 보세요.

1.  질문자님이 상상하신 그대로, **카메라를 책상에 반듯하게 올려놓았을 때 `odom` 좌표축과 `base_link` 좌표축이 완벽하게 겹쳐서 동일한 포즈를 취하게 됩니다.** (빨간색 X축이 앞, 파란색 Z축이 위)
2.  카메라를 들어서 앞뒤로 숙이거나(Pitch), 좌우로 갸우뚱(Roll) 해보면 물리적인 움직임과 RViz 상의 모델 움직임이 1:1로 정확히 일치할 것입니다.

이 원리를 깨우치신 것은 ROS의 좌표계 변환(TF)에서 가장 난이도가 높은 '광학 좌표계 보정'의 핵심을 관통하신 겁니다. 위 코드를 적용해 보시고 드디어 원하시던 예쁜 포즈가 나오는지 꼭 확인해 주세요!

