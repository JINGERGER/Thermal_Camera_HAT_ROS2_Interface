from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Thermal camera node params
    serial_port = LaunchConfiguration('serial_port')
    serial_timeout = LaunchConfiguration('serial_timeout')
    rotate_180 = LaunchConfiguration('rotate_180')

    # Static TF params (parent: gripperStator, child: thermal_camera_optical_frame)
    tf_parent_frame = LaunchConfiguration('tf_parent_frame')
    tf_child_frame = LaunchConfiguration('tf_child_frame')
    tf_x = LaunchConfiguration('tf_x')
    tf_y = LaunchConfiguration('tf_y')
    tf_z = LaunchConfiguration('tf_z')
    tf_roll = LaunchConfiguration('tf_roll')
    tf_pitch = LaunchConfiguration('tf_pitch')
    tf_yaw = LaunchConfiguration('tf_yaw')

    return LaunchDescription([
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyACM0'),
        DeclareLaunchArgument('serial_timeout', default_value='1.0'),
        DeclareLaunchArgument('rotate_180', default_value='true'),

        DeclareLaunchArgument('tf_parent_frame', default_value='gripperStator'),
        DeclareLaunchArgument('tf_child_frame', default_value='thermal_camera_optical_frame'),
        # “正上方 5cm”：默认 z=+0.05。若你系统的“上”不是 +Z，改这里或直接传参覆盖。
        DeclareLaunchArgument('tf_x', default_value='0.0'),
        DeclareLaunchArgument('tf_y', default_value='0.0'),
        DeclareLaunchArgument('tf_z', default_value='0.05'),
        DeclareLaunchArgument('tf_roll', default_value='0.0'),
        DeclareLaunchArgument('tf_pitch', default_value='0.0'),
        DeclareLaunchArgument('tf_yaw', default_value='0.0'),

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
                    'rotate_180': rotate_180,
                    'serial_port': serial_port,
                    'serial_timeout': serial_timeout,
                }
                ]
        ),

        # Static transform: gripperStator -> thermal_camera_optical_frame
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='thermal_camera_static_tf',
            output='screen',
            arguments=[
                tf_x, tf_y, tf_z,
                tf_roll, tf_pitch, tf_yaw,
                tf_parent_frame, tf_child_frame,
            ],
        ),
    ])
