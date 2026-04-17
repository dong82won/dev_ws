import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'my_realsense_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),# 런치 파일 설치
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # 설정 파일 설치
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # 🚨 3. RViz 설정 파일 설치 (이 줄을 추가하세요!)
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='won',
    maintainer_email='2dongwon@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'imu_tf_broadcaster = my_realsense_pkg.imu_tf_broadcaster:main',
            'imu_tf_watchdog = my_realsense_pkg.imu_tf_watchdog:main',
            'imu_tf_service = my_realsense_pkg.imu_tf_service:main',
        ],
    },
)
