import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'dw_simulation'

def get_recursive_data_files(directory, install_base):
    """
    directory: 소스 폴더 (예: 'models')
    install_base: 설치될 기본 경로 (예: 'share/dw_simulation')
    결과: (설치될 경로, [파일들]) 형태의 리스트 반환
    """
    data_files = []
    for root, dirs, files in os.walk(directory):
        if files:
            # 1. 소스 경로(root)를 설치 경로로 변환
            # 예: 'models/Photo_models/my_photo_frame' -> 'share/dw_simulation/models/Photo_models/my_photo_frame'
            install_dir = os.path.join(install_base, root)
            # 2. 해당 폴더 내의 모든 파일 경로 리스트업
            file_paths = [os.path.join(root, f) for f in files]
            data_files.append((install_dir, file_paths))
    return data_files

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[ # type: ignore
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch 파일 설치
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ]
    # worlds 폴더 및 하위 actor_worlds 등 계층 유지 설치
    + get_recursive_data_files('worlds', os.path.join('share', package_name))
    # models 폴더 및 하위 Photo_models, QR_models 등 모든 계층 유지 설치
    + get_recursive_data_files('models', os.path.join('share', package_name)),

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='won',
    maintainer_email='2dongwon@gmail.com',
    description='My ROS2 Simulation Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'simple_drive = dw_simulation.simple_drive:main',
            'waypoint_drive = dw_simulation.waypoint_drive:main',
            'waypoint_drive2 = dw_simulation.waypoint_drive2:main',
        ],
    },
)