#!/bin/bash
# Quick reference script for launching ZED camera with base_link configuration

# After making changes, rebuild the workspace:
cd ~/ros2_ws/src
colcon build --packages-select zed_components zed_wrapper --symlink-install
source ~/ros2_ws/install/setup.bash

# Launch ZED camera with base_link configuration:
ros2 launch zed_wrapper zed_camera.launch.py \
    camera_model:=zed2i \
    ros_params_override_path:=/home/nav2/nav2_ws/src/sam_bot_nav2_gz/config/zed_base_link.yaml

# In another terminal, verify TF tree:
# ros2 run tf2_tools view_frames
# ros2 run tf2_ros tf2_echo odom base_link
