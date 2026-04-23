#include "sam_bot_nav2_gz/sam_bot_system.hpp"

#include <chrono>
#include <cmath>
#include <limits>
#include <memory>
#include <vector>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace sam_bot_hardware
{

hardware_interface::CallbackReturn SamBotSystemHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
    hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  RCLCPP_INFO(rclcpp::get_logger("SamBotSystemHardware"), "Initializing SamBotSystemHardware...");


  // Initialize parameters
  hw_positions_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
  hw_velocities_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
  hw_commands_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());

  for (const hardware_interface::ComponentInfo & joint : info_.joints)
  {
    if (joint.command_interfaces.size() != 1)
    {
      RCLCPP_FATAL(
        rclcpp::get_logger("SamBotSystemHardware"),
        "Joint '%s' has %zu command interfaces found. 1 expected.", joint.name.c_str(),
        joint.command_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.command_interfaces[0].name != hardware_interface::HW_IF_VELOCITY)
    {
      RCLCPP_FATAL(
        rclcpp::get_logger("SamBotSystemHardware"),
        "Joint '%s' have %s command interfaces found. '%s' expected.", joint.name.c_str(),
        joint.command_interfaces[0].name.c_str(), hardware_interface::HW_IF_VELOCITY);
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces.size() != 2)
    {
      RCLCPP_FATAL(
        rclcpp::get_logger("SamBotSystemHardware"),
        "Joint '%s' has %zu state interfaces found. 2 expected.", joint.name.c_str(),
        joint.state_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION)
    {
      RCLCPP_FATAL(
        rclcpp::get_logger("SamBotSystemHardware"),
        "Joint '%s' have %s state interface. '%s' expected.", joint.name.c_str(),
        joint.state_interfaces[0].name.c_str(), hardware_interface::HW_IF_POSITION);
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY)
    {
      RCLCPP_FATAL(
        rclcpp::get_logger("SamBotSystemHardware"),
        "Joint '%s' have %s state interface. '%s' expected.", joint.name.c_str(),
        joint.state_interfaces[1].name.c_str(), hardware_interface::HW_IF_VELOCITY);
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  wheel_separation_ = 0.62; // Track width from robot dimensions (base_width + wheel_ygap*2)
  wheel_radius_ = 0.14; // From URDF wheel_radius
  
  // Initialize to zero to prevent garbage values
  latest_linear_x_ = 0.0;
  latest_angular_z_ = 0.0;

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> SamBotSystemHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (uint i = 0; i < info_.joints.size(); i++)
  {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_positions_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_velocities_[i]));
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> SamBotSystemHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (uint i = 0; i < info_.joints.size(); i++)
  {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_commands_[i]));
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn SamBotSystemHardware::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  try {
    // Create ROS Node
    node_ = std::make_shared<rclcpp::Node>("sam_bot_hardware_interface");
    executor_ = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
    executor_->add_node(node_);

    // Create Sub/Pub
    zed_odom_sub_ = node_->create_subscription<nav_msgs::msg::Odometry>(
      "/zed/zed_node/odom", 10, std::bind(&SamBotSystemHardware::zedOdomCallback, this, std::placeholders::_1));

    wheel_cmd_pub_ = node_->create_publisher<std_msgs::msg::Float64MultiArray>(
      "/wheel_commands", 10);

    // Start spinning in a separate thread
    spin_thread_ = std::make_unique<std::thread>([this]() {
      executor_->spin();
    });
  } catch (const std::exception & e) {
    RCLCPP_FATAL(
      rclcpp::get_logger("SamBotSystemHardware"),
      "Failed to activate settings: %s", e.what());
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Reset values
  for (uint i = 0; i < hw_positions_.size(); i++)
  {
    hw_positions_[i] = 0.0;
    hw_velocities_[i] = 0.0;
    hw_commands_[i] = 0.0;
  }

  RCLCPP_INFO(rclcpp::get_logger("SamBotSystemHardware"), "Successfully activated!");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn SamBotSystemHardware::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  if (executor_) {
    executor_->cancel();
  }
  if (spin_thread_ && spin_thread_->joinable()) {
    spin_thread_->join();
  }
  spin_thread_.reset();
  executor_.reset();
  node_.reset();

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type SamBotSystemHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
  std::lock_guard<std::mutex> lock(data_mutex_);
  
  // Calculate wheel velocities from ZED base velocity
  // v_left = v - (w * L / 2)
  // v_right = v + (w * L / 2)
  // But we need angular velocity of the wheel (rad/s), so divide by radius
  // omega_wheel = v_wheel / radius
  
  double v = latest_linear_x_;
  double w = latest_angular_z_;
  
  double v_left = v - (w * wheel_separation_ / 2.0);
  double v_right = v + (w * wheel_separation_ / 2.0);
  
  double omega_left = v_left / wheel_radius_;
  double omega_right = v_right / wheel_radius_;
  
  // Assign to hw_velocities_ (Assuming index 0 is Left, 1 is Right - Need to check URDF order)
  // Usually the order is determined by info_.joints order.
  // We will assume alphabetic or URDF order.
  // Let's rely on joint names if we want to be robust, but for now assuming 0=Left, 1=Right is risky.
  // Let's check joint names.
  
  for (size_t i = 0; i < info_.joints.size(); i++) {
    if (info_.joints[i].name.find("left") != std::string::npos) {
        hw_velocities_[i] = omega_left;
    } else if (info_.joints[i].name.find("right") != std::string::npos) {
        hw_velocities_[i] = omega_right;
    }
  }

  // Integrate positions
  for (size_t i = 0; i < info_.joints.size(); i++) {
    hw_positions_[i] += hw_velocities_[i] * period.seconds();
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type SamBotSystemHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  if (!wheel_cmd_pub_) return hardware_interface::return_type::OK;

  auto msg = std_msgs::msg::Float64MultiArray();
  // We want to send [LeftCmd, RightCmd]
  // Again, check mapping
  double cmd_left = 0.0;
  double cmd_right = 0.0;

  for (size_t i = 0; i < info_.joints.size(); i++) {
    if (info_.joints[i].name.find("left") != std::string::npos) {
        cmd_left = hw_commands_[i];
    } else if (info_.joints[i].name.find("right") != std::string::npos) {
        cmd_right = hw_commands_[i];
    }
  }

  msg.data.push_back(cmd_left);
  msg.data.push_back(cmd_right);
  
  wheel_cmd_pub_->publish(msg);

  return hardware_interface::return_type::OK;
}

void SamBotSystemHardware::zedOdomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
  std::lock_guard<std::mutex> lock(data_mutex_);
  latest_linear_x_ = msg->twist.twist.linear.x;
  latest_angular_z_ = msg->twist.twist.angular.z;
}

}  // namespace sam_bot_hardware

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  sam_bot_hardware::SamBotSystemHardware, hardware_interface::SystemInterface)
