#ifndef DIFFERENTIAL_STEERING__ACKERMANN_CMD_VEL_CONVERTER_HPP_
#define DIFFERENTIAL_STEERING__ACKERMANN_CMD_VEL_CONVERTER_HPP_

#include <memory>
#include <vector>
#include <utility>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>

namespace differential_steering
{

class AckermannCmdVelConverter : public rclcpp::Node
{
public:
  /**
   * @brief Constructor for AckermannCmdVelConverter
   */
  AckermannCmdVelConverter();

private:
  /**
   * @brief Callback function for cmd_vel messages
   * @param msg Twist message containing linear and angular velocity commands
   */
  void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg);

  // ROS2 publishers
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr drive_pub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr steer_pub_;

  // ROS2 subscriber
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;

  // Robot parameters
  double wheel_radius_;
  double max_steering_angle_;
  double robot_length_;
  double robot_width_;

  // Wheel positions (x, y) relative to base_link in meters
  // Order: [wheel_1, wheel_2, wheel_3, wheel_4, wheel_5, wheel_6]
  std::vector<std::pair<double, double>> wheel_positions_;
};

}  // namespace differential_steering

#endif  // DIFFERENTIAL_STEERING__ACKERMANN_CMD_VEL_CONVERTER_HPP_