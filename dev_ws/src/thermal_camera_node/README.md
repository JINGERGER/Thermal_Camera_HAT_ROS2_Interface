
# thermal_camera_node
本包为微雪 Thermal Camera HAT（USB版）在 ROS2 下的驱动节点，支持 ARM64（如 Jetson Orin NX）平台。


## 目录结构
- `thermal_camera_node/`  节点主包目录
- `thermal_camera_node/thermal_camera_publisher.py`  主节点脚本
- `launch/thermal_camera_launch.py`  启动文件
- `utils/`  工具与驱动代码


## 参数说明
所有参数均可在 launch 文件中配置：

| 参数名                                      | 默认值    | 说明                       |
|---------------------------------------------|----------|----------------------------|
| image_width                                | 80       | 图像宽度                   |
| image_height                               | 62       | 图像高度                   |
| frame_rate                                 | 25       | 帧率（Hz）                 |
| encoding                                   | bgr8     | ROS图像编码格式            |
| temporal_filter_enable                     | True     | 是否启用时域滤波           |
| rolling_average_filter_enable              | False    | 是否启用滑动平均滤波       |
| median_filter_enable                       | False    | 是否启用中值滤波           |
| median_filter_ksize5_enable                | False    | 是否启用5x5中值滤波        |
| temporal_filter_strength                   | 85       | 时域滤波强度               |
| offset_corr                                | 0.0      | 温度偏移修正（单位K）      |
| sens_factor                                | 100      | 灵敏度因子                 |
| stream_enable                              | True     | 是否连续采集               |
| start_with_header_enable                   | True     | 是否带帧头                 |
| rolling_average_temperature_minimum_frame_size | 10   | 最小温度滑动窗口帧数       |
| rolling_average_temperature_maximum_frame_size | 10   | 最大温度滑动窗口帧数       |
| use_opencv_filter                          | True     | 是否使用OpenCV滤波         |
| rotate_180                                | True     | 是否将输出图像旋转 180°（相机倒装时使用） |
| serial_port                                | /dev/ttyACM0 | 串口设备路径           |
| serial_timeout                             | 1.0      | 串口读超时（秒）           |
| tf_parent_frame                            | gripperStator | 静态 TF 的 parent frame |
| tf_child_frame                             | thermal_camera_optical_frame | 静态 TF 的 child frame |
| tf_x                                      | 0.0      | 静态 TF 平移 X（米） |
| tf_y                                      | 0.0      | 静态 TF 平移 Y（米） |
| tf_z                                      | 0.05     | 静态 TF 平移 Z（米），默认在正上方约 5cm |
| tf_roll                                   | 0.0      | 静态 TF 旋转 roll（弧度） |
| tf_pitch                                  | 0.0      | 静态 TF 旋转 pitch（弧度） |
| tf_yaw                                    | 0.0      | 静态 TF 旋转 yaw（弧度） |

## 话题

| 话题 | 说明 |
|------|------|
| `/thermal_camera/image_raw` | 伪彩色图像 (bgr8) |
| `/thermal_camera/min_max_temp` | `[min, max]` °C，滑动平均（与伪彩一致） |
| `/thermal_camera/min_max_temp_instant` | `[min, max]` °C，当前帧瞬时 |

## 典型用法
1. rviz2 彩色显示：添加 Image 显示，选择 `/thermal_camera/image_raw`，encoding 设为 bgr8。
2. 订阅温度极值：
   ```bash
   ros2 topic echo /thermal_camera/min_max_temp
   ros2 topic echo /thermal_camera/min_max_temp_instant
   ```

## 适用环境
- ROS2 Foxy/Humble/…
- Python 3.6+
- Jetson、树莓派等 ARM64


