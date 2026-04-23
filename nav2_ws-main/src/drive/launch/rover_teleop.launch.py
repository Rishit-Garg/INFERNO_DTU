#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    drive_share_dir = get_package_share_directory('drive')
    ros_ign_share_dir = get_package_share_directory('ros_gz_sim')

    urdf_path = os.path.join(drive_share_dir, 'models', 'drive', 'urdf', 'drive.urdf')
    world_path = os.path.join(drive_share_dir, 'worlds', 'maze.sdf')

    return LaunchDescription([
        # 1️⃣ Start Ignition Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ros_ign_share_dir, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': f'-r {world_path}'}.items()
        ),

        # 2️⃣ Robot State Publisher (IMMEDIATE - NO TIMER)
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'robot_description': open(urdf_path).read()},
                {'use_sim_time': True},
                {'publish_frequency': 50.0}
            ],
            output='screen'
        ),

        # 2️⃣.5 CRITICAL: Static TF for lidar (wait 1 sec for robot_state_publisher)
        TimerAction(
            period=1.0,
            actions=[
                Node(
                    package='tf2_ros',
                    executable='static_transform_publisher',
                    name='base_link_to_lidar',
                    arguments=['0.36', '-0.3', '0.14', '0', '0', '0', 'base_link', 'lidar_link'],
                    output='screen'
                )
            ]
        ),

        # 3️⃣ Clock bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='clock_bridge',
            arguments=['/world/maze_world/clock@rosgraph_msgs/msg/Clock@ignition.msgs.Clock'],
            remappings=[('/world/maze_world/clock', '/clock')],
            output='screen'
        ),

        # 4️⃣ IMU bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='imu_bridge',
            arguments=['/imu/data@sensor_msgs/msg/Imu@ignition.msgs.IMU'],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        # 5️⃣ LiDAR bridge
        TimerAction(
            period=7.0,
            actions=[Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='lidar_bridge',
            arguments=['/scan@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan'],
            parameters=[{'use_sim_time': True}],
            output='screen'
        )
        ]),

        # 6️⃣ Spawn robot
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package='ros_gz_sim',
                    executable='create',
                    arguments=[
                        '-name', 'drive',
                        '-topic', 'robot_description',
                        '-x', '0', '-y', '0', '-z', '1'
                    ],
                    parameters=[{'use_sim_time': True}],
                    output='screen'
                )
            ]
        ),

        # 7️⃣ ROS 2 Control
        TimerAction(
            period=5.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(drive_share_dir, 'launch', 'ros2_control.launch.py')
                    )
                )
            ]
        ),

        # 8️⃣ Odometry Publisher (NO declare_parameter in the script!)
        TimerAction(
            period=7.0,
            actions=[
                Node(
                    package='drive',
                    executable='odometry_publisher.py',
                    name='odometry_publisher',
                    parameters=[{'use_sim_time': True}],
                    output='screen'
                )
            ]
        ),

        # 9️⃣ Steering Converter
        TimerAction(
            period=8.0,
            actions=[
                Node(
                    package='differential_steering',
                    executable='ackermann_cmd_vel_converter',
                    name='ackermann_cmd_vel_converter',
                    parameters=[
                        {'wheel_radius': 0.1125},
                        {'max_steering_angle': 1.047},
                        {'robot_length': 1.0},
                        {'robot_width': 0.54},
                        {'use_sim_time': True}
                    ],
                    output='screen',
                    remappings=[
                        ('/cmd_vel', '/cmd_vel'),
                        ('/drive_controller/commands', '/drive_controller/commands'),
                        ('/steer_controller/commands', '/steer_controller/commands')
                    ]
                )
            ]
        ),

        # 🔟 Rover status monitor
        TimerAction(
            period=10.0,
            actions=[
                Node(
                    package='drive',
                    executable='rover_status_monitor.py',
                    name='rover_status_monitor',
                    parameters=[{'use_sim_time': True}],
                    output='screen'
                )
            ]
        ),
    ])