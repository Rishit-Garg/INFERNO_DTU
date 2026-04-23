cmake_minimum_required(VERSION 3.10)
project(drive)

# Ensure you find the necessary ROS 2 packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(xacro REQUIRED)
find_package(controller_manager REQUIRED)
find_package(velocity_controllers REQUIRED)
find_package(position_controllers REQUIRED)


# Install directories for launch, worlds, and models
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install (DIRECTORY models/${PROJECT_NAME}/meshes/
  DESTINATION share/${PROJECT_NAME}/meshes
)

install(DIRECTORY worlds/
  DESTINATION share/${PROJECT_NAME}/worlds
)

install(DIRECTORY models/
  DESTINATION share/${PROJECT_NAME}/models
)

# Install Python scripts
# Install each script individually with RENAME to remove .py extension
install(PROGRAMS scripts/drive_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME drive_node
)
install(PROGRAMS scripts/joy_to_cmdvel.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME joy_to_cmdvel
)
install(PROGRAMS scripts/drive_node_controller.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME drive_node_controller
)
install(PROGRAMS scripts/odometry_publisher.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME odometry_publisher
)
  
# Export dependencies
ament_package()