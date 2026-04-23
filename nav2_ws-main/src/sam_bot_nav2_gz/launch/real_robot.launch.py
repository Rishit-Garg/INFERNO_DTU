import launch
from launch_ros.actions import Node
from launch.actions import (
    ExecuteProcess,
    DeclareLaunchArgument,
    LogInfo,
    RegisterEventHandler,
    TimerAction,
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
    params_file = LaunchConfiguration("params_file")

    # Hardware Bringup (Replaces Simulation)
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
            'publish_map_tf': 'true',
            'ros_params_override_path': PathJoinSubstitution([
                FindPackageShare("sam_bot_nav2_gz"),
                "config",
                "zed_params_override.yaml"
            ])
        }.items()
    )

    # Nav2 Bringup
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("nav2_bringup"),
                "launch",
                "navigation_launch.py"
            ])
        ]),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': params_file,
        }.items()
    )

    # RViz
    rviz_node = Node(
        condition=IfCondition(NotSubstitution(run_headless)),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
    )

    return launch.LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=[FindPackageShare("sam_bot_nav2_gz"), "/config/nav2_params_real.yaml"],
                description="Full path to the ROS2 parameters file to use for all launched nodes",
            ),
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
            navigation,
            rviz_node,
        ]
    )
