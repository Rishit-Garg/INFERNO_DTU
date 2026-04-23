import launch
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.substitutions import (
    LaunchConfiguration,
    NotSubstitution,
    AndSubstitution,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros
import os
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    """
    Launch file for real robot manual control with ZED2i camera.
    This file does not use simulation - only real hardware components.
    RViz and relay nodes are included for visualization and topic remapping.
    """
    pkg_share = launch_ros.substitutions.FindPackageShare(
        package="sam_bot_nav2_gz"
    ).find("sam_bot_nav2_gz")
    default_model_path = os.path.join(
        pkg_share, "src/description/sam_bot_description.urdf"
    )
    default_rviz_config_path = os.path.join(pkg_share, "rviz/urdf_config.rviz")

    # Launch configurations
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")
    run_headless = LaunchConfiguration("run_headless")

    # RViz for visualization
    rviz_node = Node(
        condition=IfCondition(AndSubstitution(NotSubstitution(run_headless), use_rviz)),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # ZED2i Camera Wrapper - provides visual odometry, IMU, depth, and RGB data
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
            'camera_name': 'zed2i',
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

    # Hardware Bringup - ros2_control, robot_state_publisher, EKF
    hardware_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("sam_bot_nav2_gz"),
                "launch",
                "hardware_bringup.launch.py"
            ])
        ]),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'model': LaunchConfiguration('model'),
        }.items()
    )

    # Relay nodes for topic remapping (available for future use)
    # These allow remapping between standard topics and controller-specific topics
    relay_odom = Node(
        name="relay_odom",
        package="topic_tools",
        executable="relay",
        parameters=[
            {
                "input_topic": "/diff_drive_base_controller/odom",
                "output_topic": "/odom",
            }
        ],
        output="screen",
    )

    relay_cmd_vel = Node(
        name="relay_cmd_vel",
        package="topic_tools",
        executable="relay",
        parameters=[
            {
                "input_topic": "/cmd_vel",
                "output_topic": "/diff_drive_base_controller/cmd_vel_unstamped",
            }
        ],
        output="screen",
    )

    return launch.LaunchDescription(
        [
            DeclareLaunchArgument(
                name="model",
                default_value=default_model_path,
                description="Absolute path to robot urdf file",
            ),
            DeclareLaunchArgument(
                name="use_rviz",
                default_value="true",
                description="Start RViz for visualization",
            ),
            DeclareLaunchArgument(
                name="run_headless",
                default_value="false",
                description="Don't start RViz (headless mode)",
            ),
            DeclareLaunchArgument(
                name="rvizconfig",
                default_value=default_rviz_config_path,
                description="Absolute path to rviz config file",
            ),
            DeclareLaunchArgument(
                name="use_sim_time",
                default_value="false",
                description="Use simulation time (should be false for real robot)",
            ),
            # Launch nodes
            hardware_bringup,
            zed_wrapper,
            relay_odom,
            relay_cmd_vel,
            rviz_node,
        ]
    )

