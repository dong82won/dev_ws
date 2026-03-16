import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'custom_teleop_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # --- Launch 파일이 설치되도록 아래 1줄 추가 ---
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        # --- Config(YAML) 파일이 설치되도록 아래 1줄 추가 ---
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.yaml'))),
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
            'custom_teleop_node = custom_teleop_pkg.custom_joy_teleop:main',
        ],
    },
)
