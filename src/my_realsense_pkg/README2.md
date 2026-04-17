# 1. RGB 카메라 지원 해상도 확인 방법
에러 메시지에서 제안한 대로, ROS 2 명령어를 통해 현재 노드가 인식하는 실제 지원 목록을 바로 확인할 수 있습니다.

```bash
ros2 param describe /camera/realsense_node rgb_camera.color_profile
```

# 2. 컬러 이미지 해상도 확인
```bash
ros2 param get /camera/realsense_node rgb_camera.color_profile
```
```bash
# 깊이 이미지 해상도 확인
ros2 param get /camera/realsense_node depth_module.depth_profile
```

---

