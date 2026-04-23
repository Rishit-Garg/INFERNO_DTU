#include "differential_steering/ackermann_cmd_vel_converter.hpp"
#include <cmath>
#include <algorithm>

namespace differential_steering
{

AckermannCmdVelConverter::AckermannCmdVelConverter()
: Node("ackermann_cmd_vel_converter")
{
    // Declare parameters
    this->declare_parameter<double>("wheel_radius", 0.1125);  // From URDF wheel size
    this->declare_parameter<double>("max_steering_angle", M_PI/3);  // 60 degrees max
    this->declare_parameter<double>("robot_length", 1.0);  // Distance from front to rear axle
    this->declare_parameter<double>("robot_width", 0.54);   // Distance between left/right wheels

    // Get parameters
    this->get_parameter("wheel_radius", wheel_radius_);
    this->get_parameter("max_steering_angle", max_steering_angle_);
    this->get_parameter("robot_length", robot_length_);
    this->get_parameter("robot_width", robot_width_);

    // Initialize wheel positions based on URDF (x, y coordinates relative to base_link)
    // Order: [wheel_1, wheel_2, wheel_3, wheel_4, wheel_5, wheel_6]
    wheel_positions_ = {
        {-0.52014, -0.27},  // Wheel 1: Front Left
        {0.042287, -0.27},  // Wheel 2: Front Right
        {0.47299, -0.225},  // Wheel 3: Middle Left
        {-0.51862, 0.27},   // Wheel 4: Middle Right
        {0.0438, 0.27},     // Wheel 5: Rear Left
        {0.47715, 0.225}    // Wheel 6: Rear Right
    };

    // Publishers for individual wheel control
    drive_pub_ = this->create_publisher<std_msgs::msg::Float64MultiArray>("/drive_controller/commands", 10);
    steer_pub_ = this->create_publisher<std_msgs::msg::Float64MultiArray>("/steer_controller/commands", 10);

    // Subscriber for velocity commands
    cmd_vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
        "/cmd_vel", 10,
        std::bind(&AckermannCmdVelConverter::cmdVelCallback, this, std::placeholders::_1));
}

void AckermannCmdVelConverter::cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
{
  double linear_x = msg->linear.x;
    double angular_z = msg->angular.z;
    
    linear_x=linear_x*-1;
    
    

    // Wheel rotational speeds (rad/s)
    std::vector<double> wheel_speeds(6, 0.0);

    // Steering angles are unused in skid steering but kept for compatibility (always 0)
    std::vector<double> steering_angles(6, 0.0);

    // Calculate linear speeds of left and right wheels
    double half_width = robot_width_ / 2.0;
    double left_linear = 0;
    double right_linear = 0;
    if (linear_x==0 and angular_z!=0)
    {
    if (angular_z>0)
    {
        left_linear = -(angular_z * half_width);
        right_linear = angular_z * half_width;
        //only right wheels move now

    }
    else
    {
        right_linear = angular_z * half_width;
        left_linear = -(angular_z * half_width);
        //only left wheels move now
        
    }
    
    

    // Convert to angular velocity (rad/s) for wheels
    double left_speed = left_linear / wheel_radius_;
    double right_speed = right_linear / wheel_radius_;

    // Assign speeds based on left/right wheels
    
    wheel_speeds[3] = left_speed;
    wheel_speeds[4] = left_speed;
    wheel_speeds[5] = left_speed;

    
    wheel_speeds[0] = -right_speed;
    wheel_speeds[1] = -right_speed;
    wheel_speeds[2] = right_speed;
      

    
    }
    if (linear_x!=0 and angular_z==0)
    {

    wheel_speeds[0] = -linear_x;
    wheel_speeds[2] = linear_x;
    wheel_speeds[4] = linear_x;
    wheel_speeds[1] = -linear_x;
    wheel_speeds[3] = linear_x;
    wheel_speeds[5] = linear_x;
    //now every wheel have same speed and direction
    }

    
    

    
    // Publish drive and zero steering
    std_msgs::msg::Float64MultiArray drive_msg;

    drive_msg.data = wheel_speeds;

    drive_pub_->publish(drive_msg);
    

    // Debug logging
    RCLCPP_DEBUG(this->get_logger(),
                "Skid Cmd: vx=%.2f, wz=%.2f", linear_x, angular_z);
    RCLCPP_DEBUG(this->get_logger(),
                "Wheel Speeds (rad/s): [%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]",
                wheel_speeds[0], wheel_speeds[1], wheel_speeds[2],
                wheel_speeds[3], wheel_speeds[4], wheel_speeds[5]);


}
}  
// namespace differential_steering

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<differential_steering::AckermannCmdVelConverter>());
    rclcpp::shutdown();
    return 0;
}
