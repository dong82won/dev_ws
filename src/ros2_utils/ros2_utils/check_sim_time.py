#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("🔍 ROS 2 노드별 use_sim_time 파라미터 검사 시작...\n")
    print("-" * 50)
  
    # 1. 실행 중인 모든 노드 목록 가져오기
    try:
        result = subprocess.run(['ros2', 'node', 'list'], capture_output=True, text=True, check=True)
        nodes = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("❌ ROS 2 노드 목록을 가져오는데 실패했습니다. (데몬이 켜져 있는지 확인하세요)")
        sys.exit(1)

    if not nodes or nodes == ['']:
        print("⚠️ 실행 중인 ROS 2 노드가 없습니다.")
        sys.exit(0)

    # 2. 각 노드를 순회하며 파라미터 조회
    for node in nodes:
        # 노드 이름 출력 (노란색)
        print(f"\033[1;33m[{node}]\033[0m")
        try:
            # ros2 param get 명령어 실행 (타임아웃 1.0초)
            param_result = subprocess.run(
                ['ros2', 'param', 'get', node, 'use_sim_time'],
                capture_output=True,
                text=True,
                timeout=1.0
            )

            output = param_result.stdout.strip()
            error = param_result.stderr.strip()

            # 결과물 예쁘게 출력하기
            if "True" in output:
                print("  \033[1;32m✅ Boolean value is: True\033[0m")
            elif "False" in output:
                print("  \033[1;31m❌ Boolean value is: False\033[0m")
            elif "not set" in error or "not set" in output:
                print("  \033[1;30m➖ Parameter not set (무시해도 됨)\033[0m")
            else:
                print(f"  ⚠️ {error if error else output}")

        except subprocess.TimeoutExpired:
            print("  \033[1;31m⏱️ (No response or timeout)\033[0m")

        print("-" * 50)

    print("\n✅ 검사가 완료되었습니다.")

if __name__ == '__main__':
    main()