"""
Manual Control Launch File for Real Robot with EKF
--------------------------------------------------
Launches hardware bringup, ZED camera, EKF, and teleop for manual control.
No navigation stack - just pure teleoperation with sensor fusion.
"""

import launch
from launch_ros.actions import Node
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    NotSubstitution,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Arguments
    run_headless = LaunchConfiguration("run_headless")

    # Hardware Bringup (ros2_control, robot_state_publisher, controllers)
    hardware_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("sam_bot_nav2_gz"),
                "launch",
                "hardware_bringup.launch.py"
            ])
        ]),
        launch_arguments={'use_sim_time': 'false'}.items()
    )

    # ZED Wrapper
    zed_wrapper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("zed_wrapper"),
                "launch",
                "zed_camera.launch.py"
            ])
        ]),
        launch_arguments={
            'camera_model': 'zed2i',
            'camera_name': 'zed',
            'publish_urdf': 'false',
            'publish_tf': 'false',
            'publish_map_tf': 'false',
            'ros_params_override_path': PathJoinSubstitution([
                FindPackageShare("sam_bot_nav2_gz"),
                "config",
                "zed_params_override.yaml"
            ])
        }.items()
    )

    # EKF Node for sensor fusion (ZED VIO + IMU)
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            PathJoinSubstitution([
                FindPackageShare("sam_bot_nav2_gz"),
                "config",
                "ekf_manual_control.yaml"
            ]),
            {'use_sim_time': False}
        ]
    )

    # Teleop Twist Keyboard Node
    teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        prefix='xterm -e',  # Opens in new terminal for keyboard input
        remappings=[
            ('cmd_vel', '/cmd_vel')
        ]
    )

    # Serial Command Bridge (sends wheel commands to motors)
    cmd_serial_node = Node(
        package='drive',
        executable='cmd_serial.py',
        name='cmd_serial_node',
        output='screen',
        remappings=[
            ('cmd_vel_nav', '/cmd_vel')  # Subscribe to teleop commands
        ]
    )

    # RViz for visualization
    rviz_node = Node(
        condition=IfCondition(NotSubstitution(run_headless)),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
    )

    return launch.LaunchDescription([
        DeclareLaunchArgument(
            name="rvizconfig",
            default_value=[
                FindPackageShare("sam_bot_nav2_gz"),
                "/rviz/navigation_config.rviz",
            ],
            description="Absolute path to rviz config file",
        ),
        DeclareLaunchArgument(
            name="run_headless",
            default_value="False",
            description="Don't start RViz",
        ),
        hardware_bringup,
        zed_wrapper,
        ekf_node,
        teleop_node,
        cmd_serial_node,
        rviz_node,
    ])
