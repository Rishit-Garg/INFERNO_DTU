#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    drive_share_dir = get_package_share_directory('drive')
    controller_config = os.path.join(drive_share_dir, 'models', 'drive', 'config', 'rover_controllers.yaml')

    return LaunchDescription([
        # Load controller manager configuration
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[controller_config],
            output='screen',
        ),

        # Spawn joint_state_broadcaster
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        ),

        # Spawn drive controller
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['drive_controller'],
            output='screen',
        ),

        # Spawn steer controller
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['steer_controller'],
            output='screen',
        ),
    ])