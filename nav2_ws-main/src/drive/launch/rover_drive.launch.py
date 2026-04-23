from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    # Joy node
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen'
    )

    # Drive node controller
    drive_node_controller = Node(
        package='drive',
        executable='drive_node_controller',
        name='drive_node_controller',
        output='screen'
    )

    # Joy to cmd_vel converter
    joytocmdvel_node = Node(
        package='drive',
        executable='joy_to_cmdvel',
        name='joy_to_cmdvel',
        output='screen'
    )

    # Include sam_bot_nav2_gz display launch file
    display_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('sam_bot_nav2_gz'),
                'launch',
                'display.launch.py'
            ])
        ]),
        launch_arguments={
            'use_sim': 'false',
            'use_sim_time': 'false',
            'model': PathJoinSubstitution([
                FindPackageShare('sam_bot_nav2_gz'),
                'src',
                'description',
                'sam_bot_description.urdf'
            ])
        }.items()
    )

    return LaunchDescription([
        joy_node,
        drive_node_controller,
        joytocmdvel_node,
        display_launch,
    ])
