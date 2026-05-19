#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERIAL_PORT="${SERIAL_PORT:-/dev/ttyACM0}"

echo "Starting Thermal Camera HAT ROS2 Interface..."
if [ -e "$SERIAL_PORT" ]; then
    sudo /bin/chmod 666 "$SERIAL_PORT"
    echo "Permissions set for $SERIAL_PORT"
else
    echo "Warning: $SERIAL_PORT not found; plug in the camera or set SERIAL_PORT"
fi

if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
elif [ -f /opt/ros/foxy/setup.bash ]; then
    source /opt/ros/foxy/setup.bash
fi

source "$SCRIPT_DIR/dev_ws/install/setup.bash"
echo "Starting thermal camera node on $SERIAL_PORT ..."
ros2 launch "$SCRIPT_DIR/dev_ws/src/thermal_camera_node/launch/thermal_camera_launch.py" \
    serial_port:="$SERIAL_PORT"
