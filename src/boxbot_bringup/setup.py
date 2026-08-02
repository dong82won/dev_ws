import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'boxbot_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 런치 파일 전체 설치 (.launch.py, .py, .xml 등 모두 포함)
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
        # 설정 파일 전체 설치 (하위 경로 포함 안전성 확보)
        (os.path.join('share', package_name, 'config'), glob('config/*')),
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
        ],
    },
)
