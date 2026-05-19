from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='thermal_camera_node',
            executable='thermal_camera_publisher',
            name='thermal_camera_node',
            output='screen',
            parameters=[
                {
                    'image_width': 80,
                    'image_height': 62,
                    'frame_rate': 25,
                    'encoding': 'bgr8',
                    'temporal_filter_enable': True,
                    'rolling_average_filter_enable': False,
                    'median_filter_enable': False,
                    'median_filter_ksize5_enable': False,
                    'temporal_filter_strength': 85,
                    'offset_corr': 0.0,
                    'sens_factor': 100,
                    'stream_enable': True,
                    'start_with_header_enable': True,
                    'rolling_average_temperature_minimum_frame_size': 10,
                    'rolling_average_temperature_maximum_frame_size': 10,
                    'use_opencv_filter': True,
                    'serial_port': '/dev/ttyACM0',
                    'serial_timeout': 1.0,
                }
                ]
        )
    ])
