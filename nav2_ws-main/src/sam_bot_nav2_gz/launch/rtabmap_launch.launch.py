from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    
    # Get path to config file
    pkg_share = get_package_share_directory('sam_bot_nav2_gz')
    config_file = os.path.join(pkg_share, 'config', 'rtabmap_params.yaml')
    
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[config_file],
        remappings=[
            ('rgb/image', '/zed/zed_node/rgb/color/rect/image'),
            ('depth/image', '/zed/zed_node/depth/depth_registered'),
            ('rgb/camera_info', '/zed/zed_node/rgb/color/rect/camera_info'),
            ('odom', '/zed/zed_node/odom'),
            ('imu', '/zed/zed_node/imu/data'),
        ],
    )
    
    return LaunchDescription([
        rtabmap_node,
    ])