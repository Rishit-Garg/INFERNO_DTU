from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Hardware bringup launch file for real robot.
    Launches ros2_control, robot_state_publisher, controller spawners, and EKF.
    This file is configured for REAL HARDWARE (not simulation).
    """
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock - should be FALSE for real robot",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "model",
            default_value=PathJoinSubstitution(
                [FindPackageShare("sam_bot_nav2_gz"), "src", "description", "sam_bot_description.urdf"]
            ),
            description="Absolute path to robot urdf file",
        )
    )

    # Initialize Arguments
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Get URDF via xacro - use_sim:=false ensures real hardware configuration
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            LaunchConfiguration("model"),
            " ",
            "use_sim:=false",  # CRITICAL: This must be false for real hardware
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("sam_bot_nav2_gz"),
            "config",
            "diff_drive_controller_velocity.yaml",
        ]
    )

    # Nodes
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        output="both",
        remappings=[
            ("/diff_drive_base_controller/cmd_vel_unstamped", "/cmd_vel"),
        ],
    )
    
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_base_controller", "--controller-manager", "/controller_manager"],
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            PathJoinSubstitution([FindPackageShare("sam_bot_nav2_gz"), "config", "ekf.yaml"]),
            {'use_sim_time': use_sim_time}
        ]
    )

    ekf_global_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_global',
        output='screen',
        parameters=[
            PathJoinSubstitution([FindPackageShare("sam_bot_nav2_gz"), "config", "ekf_global.yaml"]),
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('odometry/filtered', 'odometry/global')
        ]
    )

    navsat_transform_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform',
        output='screen',
        parameters=[
            PathJoinSubstitution([FindPackageShare("sam_bot_nav2_gz"), "config", "navsat_transform.yaml"]),
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('imu/data', '/zed/zed_node/imu/data'),
            ('gps/fix', '/gps/fix'), 
            ('odometry/filtered', '/odometry/filtered')
        ]
    )
    
    nodes = [
        control_node,
        robot_state_pub_node,
        joint_state_broadcaster_spawner,
        robot_controller_spawner,
        ekf_node,
        ekf_global_node,
        navsat_transform_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
