#ifndef SAM_BOT_NAV2_GZ__SAM_BOT_SYSTEM_HPP_
#define SAM_BOT_NAV2_GZ__SAM_BOT_SYSTEM_HPP_

#include <memory>
#include <string>
#include <vector>
#include <mutex>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp_lifecycle/state.hpp"
#include "sam_bot_nav2_gz/visibility_control.h"

#include "nav_msgs/msg/odometry.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"

namespace sam_bot_hardware
{
class SamBotSystemHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(SamBotSystemHardware)

  SAM_BOT_NAV2_GZ_PUBLIC
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  SAM_BOT_NAV2_GZ_PUBLIC
  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  SAM_BOT_NAV2_GZ_PUBLIC
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  SAM_BOT_NAV2_GZ_PUBLIC
  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  SAM_BOT_NAV2_GZ_PUBLIC
  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  SAM_BOT_NAV2_GZ_PUBLIC
  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  SAM_BOT_NAV2_GZ_PUBLIC
  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // ROS Node for subscribing to ZED and publishing commands
  rclcpp::Node::SharedPtr node_;
  rclcpp::executors::SingleThreadedExecutor::SharedPtr executor_;
  std::unique_ptr<std::thread> spin_thread_;
  
  // Pub/Sub
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr zed_odom_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr wheel_cmd_pub_;

  // Callbacks
  void zedOdomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);

  // Data storage
  std::vector<double> hw_commands_;
  std::vector<double> hw_positions_;
  std::vector<double> hw_velocities_;

  // Parameters
  double wheel_separation_;
  double wheel_radius_;

  // Thread safety
  std::mutex data_mutex_;
  
  // Latest ZED data
  double latest_linear_x_ = 0.0;
  double latest_angular_z_ = 0.0;
  rclcpp::Time last_zed_time_;
};

}  // namespace sam_bot_hardware

#endif  // SAM_BOT_NAV2_GZ__SAM_BOT_SYSTEM_HPP_
