# Thermal Camera HAT ROS2 Interface

基于 [微雪 Thermal Camera HAT（USB 版）](https://www.waveshare.net/wiki/Thermal_Camera_HAT) 的 ROS2 驱动，在 x86_64 / ARM64（如 Jetson Orin NX、ThinkPad）上测试可用。

## 功能

| 话题 | 类型 | 说明 |
|------|------|------|
| `/thermal_camera/image_raw` | `sensor_msgs/Image` | 伪彩色热图，`bgr8`，默认 JET 色图 |
| `/thermal_camera/min_max_temp` | `std_msgs/Float32MultiArray` | `data[0]` 全图最低温、`data[1]` 最高温（°C），**10 帧滑动平均**，与伪彩拉伸一致 |
| `/thermal_camera/min_max_temp_instant` | `std_msgs/Float32MultiArray` | 同上，**当前帧瞬时**极值，响应更快 |

## 近期更新

- **修复 `senxor` 模块**：`colcon build` 后正确安装 `utils/senxor` 为 Python 包，无需手动改 `sys.path`
- **串口**：默认 `/dev/ttyACM0`，支持 `serial_port` 参数；`start_thermal_camera_node.sh` 自动 `chmod` 并传入 launch
- **依赖**：移除启动时对 `matplotlib`/`cmapy` 的硬依赖（按需延迟加载），`requirements.txt` 仅保留运行必需项
- **温度发布**：`Float32MultiArray` 使用 Python `float`；新增瞬时温度话题
- **稳定性**：串口读超时、`mi48.stop()` 优雅退出、按相机实际 FPS  pacing 读帧（避免定时器快于 USB 帧率导致堆积）
- **CRC**：帧 CRC 错误时跳过发布并告警

## 环境要求

- ROS 2 **Humble**（或 Foxy，启动脚本会自动检测）
- Python 3.10+
- USB 热像仪（默认枚举为 `/dev/ttyACM0`）

## 快速开始

### 1. 依赖

参考 [微雪 Wiki](https://www.waveshare.net/wiki/Thermal_Camera_HAT)，或：

```bash
pip install -r requirements.txt
```

### 2. 编译

```bash
cd dev_ws
colcon build --packages-select thermal_camera_node
source install/setup.bash
```

### 3. 运行

**推荐**（含串口权限，自动选择 Humble/Foxy）：

```bash
chmod +x ./start_thermal_camera_node.sh
./start_thermal_camera_node.sh
```

其他方式：

```bash
# 需先授权串口，例如：
sudo chmod 666 /dev/ttyACM0

cd dev_ws && source install/setup.bash
ros2 launch src/thermal_camera_node/launch/thermal_camera_launch.py
```

```bash
cd dev_ws && source install/setup.bash
ros2 run thermal_camera_node thermal_camera_publisher --ros-args -p serial_port:=/dev/ttyACM0
```

非默认串口：

```bash
SERIAL_PORT=/dev/ttyACM1 ./start_thermal_camera_node.sh
```

### 4. 查看数据

```bash
ros2 topic echo /thermal_camera/min_max_temp_instant
ros2 topic hz /thermal_camera/image_raw
```

rviz2：添加 **Image**，Topic 选 `/thermal_camera/image_raw`，Encoding 选 `bgr8`。

> 使用前请摘掉镜头保护罩，否则温度与图像对比度会明显偏低。

## 参数配置

在 `dev_ws/src/thermal_camera_node/launch/thermal_camera_launch.py` 或命令行 `--ros-args -p` 中修改。

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `image_width` | 80 | 图像宽度（像素） |
| `image_height` | 62 | 图像高度（像素） |
| `frame_rate` | 25 | 请求帧率（Hz）；实际受 USB/相机限制，节点会自动取 `min(请求, 相机当前 FPS)` |
| `encoding` | bgr8 | 图像编码 |
| `serial_port` | `/dev/ttyACM0` | 串口设备路径 |
| `serial_timeout` | 1.0 | 串口读超时（秒） |
| `temporal_filter_enable` | True | 相机端时域滤波 |
| `rolling_average_filter_enable` | False | 相机端滑动平均滤波 |
| `median_filter_enable` | False | 相机端中值滤波 |
| `median_filter_ksize5_enable` | False | 5×5 中值滤波 |
| `temporal_filter_strength` | 85 | 时域滤波强度 |
| `offset_corr` | 0.0 | 温度偏移（K） |
| `sens_factor` | 100 | 灵敏度因子（%） |
| `stream_enable` | True | 连续采集 |
| `start_with_header_enable` | True | 帧带 SPI 头 |
| `rolling_average_temperature_minimum_frame_size` | 10 | 发布用最低温滑动窗口帧数 |
| `rolling_average_temperature_maximum_frame_size` | 10 | 发布用最高温滑动窗口帧数 |
| `use_opencv_filter` | True | 中值 + 双边滤波后再伪彩 |
| `rotate_180` | True | 将输出图像旋转 180°（默认开启，适用于相机倒装/画面上下颠倒） |
| `tf_parent_frame` | gripperStator | 静态 TF 的 parent frame |
| `tf_child_frame` | thermal_camera_optical_frame | 静态 TF 的 child frame（与图像 `frame_id` 对齐） |
| `tf_x` | 0.0 | 静态 TF 平移 X（米） |
| `tf_y` | 0.0 | 静态 TF 平移 Y（米） |
| `tf_z` | 0.05 | 静态 TF 平移 Z（米），默认在 `gripperStator` 正上方约 5cm |
| `tf_roll` | 0.0 | 静态 TF 旋转 roll（弧度） |
| `tf_pitch` | 0.0 | 静态 TF 旋转 pitch（弧度） |
| `tf_yaw` | 0.0 | 静态 TF 旋转 yaw（弧度） |

## 目录结构

```
Thermal_Camera_HAT_ROS2_Interface/
├── dev_ws/src/thermal_camera_node/   # ROS2 功能包
│   ├── thermal_camera_node/         # 节点
│   ├── utils/senxor/                # MI48 USB 驱动
│   └── launch/
├── requirements.txt
└── start_thermal_camera_node.sh
```

## 故障排除

| 现象 | 处理 |
|------|------|
| `No module named 'senxor'` | `colcon build` 后 `source dev_ws/install/setup.bash` |
| `Failed to connect` / 无 `/dev/ttyACM0` | 插紧 USB；`ls /dev/ttyACM*`；`SERIAL_PORT=... ./start_thermal_camera_node.sh` |
| `ModuleNotFoundError: crcmod` 等 | `pip install -r requirements.txt` |
| 温度偏低、图像发灰 | 摘掉保护罩；观察 `min_max_temp_instant` |
| 退出后无法再次打开串口 | 已支持 `Ctrl+C` 时 `mi48.stop()`；若仍占用可 `sudo fuser -k /dev/ttyACM0` |

## rviz2 测试

![rviz2 测试](https://imgbed.yesord.top/file/github/1753774880194_微信截图_20250729153847.png)

## 致谢

- 上游：[Yesord/Thermal_Camera_HAT_ROS2_Interface](https://github.com/Yesord/Thermal_Camera_HAT_ROS2_Interface)
- 本仓库继续开发：[JINGERGER/Thermal_Camera_HAT_ROS2_Interface](https://github.com/JINGERGER/Thermal_Camera_HAT_ROS2_Interface)
