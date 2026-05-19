from setuptools import setup

package_name = 'thermal_camera_node'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name, 'senxor'],
    package_dir={
        package_name: package_name,
        'senxor': 'utils/senxor',
    },
    package_data={
        'senxor': ['distance_correction.dat'],
    },
    data_files=[('share/ament_index/resource_index/packages', ['resource/' + package_name]),
                ('share/' + package_name, ['package.xml'])],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Nolen Hsu',
    maintainer_email='2691004662@qq.com',
    description='集成和发布热成像摄像头数据的ROS2包',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'thermal_camera_publisher = thermal_camera_node.thermal_camera_publisher:main'
        ],
    },
)
