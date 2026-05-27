#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
import cv2
import numpy as np
import logging
import os

from senxor.mi48 import MI48
from senxor.utils import data_to_frame, remap, cv_filter, RollingAverageFilter, connect_senxor


class ThermalCameraNode(Node):
    def __init__(self):
        super().__init__('thermal_camera_node')
        self.image_pub_ = self.create_publisher(Image, 'thermal_camera/image_raw', 10)
        # 10 帧滑动平均后的全图 min/max (°C)，用于稳定显示与伪彩拉伸
        self.temp_pub_ = self.create_publisher(
            Float32MultiArray, 'thermal_camera/min_max_temp', 10)
        # 当前帧瞬时全图 min/max (°C)，响应更快
        self.temp_instant_pub_ = self.create_publisher(
            Float32MultiArray, 'thermal_camera/min_max_temp_instant', 10)

        self.declare_parameter('image_width', 80)
        self.declare_parameter('image_height', 62)
        self.declare_parameter('frame_rate', 25)
        self.declare_parameter('encoding', 'bgr8')
        self.declare_parameter('temporal_filter_enable', True)
        self.declare_parameter('rolling_average_filter_enable', False)
        self.declare_parameter('median_filter_enable', False)
        self.declare_parameter('median_filter_ksize5_enable', False)
        self.declare_parameter('temporal_filter_strength', 85)
        self.declare_parameter('offset_corr', 0.0)
        self.declare_parameter('sens_factor', 100)
        self.declare_parameter('stream_enable', True)
        self.declare_parameter('start_with_header_enable', True)
        self.declare_parameter('rolling_average_temperature_minimum_frame_size', 10)
        self.declare_parameter('rolling_average_temperature_maximum_frame_size', 10)
        self.declare_parameter('use_opencv_filter', True)
        self.declare_parameter('rotate_180', True)
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('serial_timeout', 1.0)

        self.logger = logging.getLogger('thermal_camera_node')
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        self.frame_rate = self.get_parameter('frame_rate').value
        self.encoding = self.get_parameter('encoding').value
        self.temporal_filter_enable = self.get_parameter('temporal_filter_enable').value
        self.rolling_average_filter_enable = self.get_parameter('rolling_average_filter_enable').value
        self.median_filter_enable = self.get_parameter('median_filter_enable').value
        self.median_filter_ksize5_enable = self.get_parameter('median_filter_ksize5_enable').value
        self.temporal_filter_strength = self.get_parameter('temporal_filter_strength').value
        self.offset_corr = self.get_parameter('offset_corr').value
        self.sens_factor = self.get_parameter('sens_factor').value
        self.stream_enable = self.get_parameter('stream_enable').value
        self.start_with_header_enable = self.get_parameter('start_with_header_enable').value
        self.rolling_average_temperature_minimum_frame_size = self.get_parameter(
            'rolling_average_temperature_minimum_frame_size').value
        self.rolling_average_temperature_maximum_frame_size = self.get_parameter(
            'rolling_average_temperature_maximum_frame_size').value
        self.use_opencv_filter = self.get_parameter('use_opencv_filter').value
        self.rotate_180 = self.get_parameter('rotate_180').value
        self.serial_port = self.get_parameter('serial_port').value
        self.serial_timeout = self.get_parameter('serial_timeout').value

        self.mi48 = None
        self._frame_timer = None
        self._shutting_down = False

        self.mi48, self.connected_port, self.port_names = connect_senxor(
            self.serial_port, serial_timeout=self.serial_timeout)
        if self.mi48 is None:
            self.get_logger().error(
                f"Failed to connect on {self.serial_port!r}. "
                f"Auto-detected MI ports: {self.port_names}. "
                f"Check USB cable and run: sudo chmod 666 {self.serial_port}"
            )
            raise RuntimeError("No camera found")
        self.logger.info(f'Camera info: {self.mi48.camera_info}')

        self.mi48.set_fps(self.frame_rate)
        self.mi48.disable_filter(
            f1=not self.temporal_filter_enable,
            f2=not self.rolling_average_filter_enable,
            f3=not self.median_filter_enable)
        self.mi48.set_filter_1(self.temporal_filter_strength)
        self.mi48.enable_filter(
            f1=self.temporal_filter_enable,
            f2=self.rolling_average_filter_enable,
            f3=self.median_filter_enable,
            f3_ks_5=self.median_filter_ksize5_enable)
        self.mi48.set_offset_corr(self.offset_corr)
        self.mi48.set_sens_factor(self.sens_factor)
        self.mi48.get_sens_factor()
        self.mi48.start(stream=self.stream_enable, with_header=self.start_with_header_enable)

        self.dminav = RollingAverageFilter(
            N=self.rolling_average_temperature_minimum_frame_size)
        self.dmaxav = RollingAverageFilter(
            N=self.rolling_average_temperature_maximum_frame_size)

        actual_fps = float(self.mi48.get_fps())
        self._effective_fps = min(float(self.frame_rate), actual_fps)
        if self._effective_fps < 1.0:
            self._effective_fps = 1.0
        self.get_logger().info(
            f'Frame pacing: {self._effective_fps:.2f} Hz '
            f'(requested {self.frame_rate}, camera reports {actual_fps:.2f})')

        self._grab_and_publish()
        self._schedule_next_frame()

    def _schedule_next_frame(self):
        if self._shutting_down:
            return
        if self._frame_timer is not None:
            self._frame_timer.cancel()
        period = 1.0 / self._effective_fps
        self._frame_timer = self.create_timer(period, self._on_frame_timer)

    def _on_frame_timer(self):
        if self._frame_timer is not None:
            self._frame_timer.cancel()
            self._frame_timer = None
        if self._shutting_down:
            return
        self._grab_and_publish()
        self._schedule_next_frame()

    def _grab_and_publish(self):
        data, header = self.mi48.read()
        if data is None:
            self.get_logger().error('NONE data received instead of GFRA')
            return
        if getattr(self.mi48, 'crc_error', False):
            self.get_logger().warn('Frame CRC error; skipping publish')
            return

        min_instant = float(data.min())
        max_instant = float(data.max())
        min_temp = float(self.dminav(min_instant))
        max_temp = float(self.dmaxav(max_instant))

        smooth_msg = Float32MultiArray()
        smooth_msg.data = [min_temp, max_temp]
        self.temp_pub_.publish(smooth_msg)

        instant_msg = Float32MultiArray()
        instant_msg.data = [min_instant, max_instant]
        self.temp_instant_pub_.publish(instant_msg)

        frame = data_to_frame(data, (self.image_width, self.image_height), hflip=False)
        frame = np.clip(frame, min_temp, max_temp)

        img_data = remap(frame)
        if self.use_opencv_filter:
            filt_uint8 = cv_filter(
                img_data,
                {'blur_ks': 3, 'd': 5, 'sigmaColor': 27, 'sigmaSpace': 27},
                use_median=True, use_bilat=True, use_nlm=False)
        else:
            filt_uint8 = img_data

        try:
            img_color = cv2.applyColorMap(filt_uint8, cv2.COLORMAP_JET)
            if self.rotate_180:
                img_color = cv2.rotate(img_color, cv2.ROTATE_180)
            msg = Image()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'thermal_camera_optical_frame'
            msg.height = img_color.shape[0]
            msg.width = img_color.shape[1]
            msg.encoding = self.encoding
            msg.is_bigendian = 0
            msg.step = img_color.shape[1] * 3
            msg.data = img_color.tobytes()
            self.image_pub_.publish(msg)
        except Exception as e:
            self.get_logger().warn(f'cv2 colormap failed: {e}, fallback to mono8.')
            msg = Image()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'thermal_camera_optical_frame'
            msg.height = img_data.shape[0]
            msg.width = img_data.shape[1]
            msg.encoding = 'mono8'
            msg.is_bigendian = 0
            msg.step = img_data.shape[1]
            mono = filt_uint8
            if self.rotate_180:
                mono = cv2.rotate(mono, cv2.ROTATE_180)
            msg.data = mono.tobytes()
            self.image_pub_.publish(msg)

    def destroy_node(self):
        self._shutting_down = True
        if self._frame_timer is not None:
            self._frame_timer.cancel()
            self._frame_timer = None
        if self.mi48 is not None:
            try:
                self.get_logger().info('Stopping thermal camera capture...')
                self.mi48.stop()
            except Exception as exc:
                self.get_logger().warn(f'Error while stopping camera: {exc}')
            self.mi48 = None
        super().destroy_node()

    def timer_callback(self):
        """Deprecated alias; kept for compatibility if referenced elsewhere."""
        self._grab_and_publish()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ThermalCameraNode()
        node.get_logger().info('Thermal camera node started successfully.')
        rclpy.spin(node)
    except Exception as e:
        print(f'thermal_camera_node failed: {e}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
