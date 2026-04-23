cmake_minimum_required(VERSION 3.8)
project(differential_steering)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Include directories
include_directories(include)

# Add executable
add_executable(ackermann_cmd_vel_converter 
  src/ackermann_cmd_vel_converter.cpp
)

# Specify dependencies
ament_target_dependencies(ackermann_cmd_vel_converter
  rclcpp
  geometry_msgs
  std_msgs
)

# Install executable
install(TARGETS
  ackermann_cmd_vel_converter
  DESTINATION lib/${PROJECT_NAME}
)

# Install include directories
install(DIRECTORY include/
  DESTINATION include/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()