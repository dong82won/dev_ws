::: mermaid
graph TD
    subgraph "최상위 애플리케이션 계층 (Application Layer)"
        Nav2
        SLAM
    end

    subgraph "ROS 2 통신 인터페이스 (Communication Layer)"
        CmdVel
        CMSrv
        JSTopic
        TF
    end

    subgraph "제어 프레임워크 계층 (ros2_control)"
        subgraph "컨트롤러 매니저 노드 (Controller Manager Node)"
            direction TB
            
            subgraph "컨트롤러 플러그인 (Controllers)"
                DDC
                JSB
            end
            
            subgraph "중앙 관리 모듈 (Core Modules)"
                RM
            end
        end
        
        subgraph "하드웨어 추상화 계층 (Hardware Abstraction)"
            HI[Hardware Interface Plugin]
        end
    end

    subgraph "물리/시뮬레이션 계층 (Physical Layer)"
        HW
    end

    %% 데이터 흐름 및 연동 관계
    Nav2 -->|목표 속도 전송| CmdVel
    CmdVel --> DDC
    
    SLAM -->|위치 보정 데이터| TF
    
    DDC -->|바퀴 속도 계산 및 요청| RM
    RM -->|명령 쓰기 Write| HI
    HI -->|전기 신호/API 호출| HW
    
    HW -->|센서/엔코더 피드백| HI
    HI -->|상태 읽기 Read| RM
    RM -->|조인트 정보 업데이트| JSB
    
    JSB -->|상태 게시| JSTopic
    DDC -->|오도메트리 발행| TF
    
    CMSrv -.->|제어기 생명주기 관리| CMSrv
    CMSrv -.->|로드/활성화 명령| DDC
    CMSrv -.->|로드/활성화 명령| JSB
:::