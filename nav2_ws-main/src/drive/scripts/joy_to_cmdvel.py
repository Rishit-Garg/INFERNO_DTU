#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class JoyToCmdVel(Node):
    def __init__(self):
        super().__init__('joy_to_cmdvel')
        
        # Declare parameters with default values
        # Defaulting value to 1.0 for scale
        self.declare_parameter('linear_scale', 1.0)
        self.declare_parameter('angular_scale', 1.0)
        
        # Defaulting Axis 1 for Linear and Axis 2 for Angular as requested
        # Note: on many controllers, Axis 1 is Left Stick Vertical, and Axis 2 is often LT (Trigger) or Right Stick Horizontal depending on mode/driver.
        self.declare_parameter('axis_linear', 1) 
        self.declare_parameter('axis_angular', 2)

        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10)
        
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.get_logger().info("Joy to CmdVel Node Started. Listening on /joy")

    def joy_callback(self, msg):
        twist = Twist()
        
        # Get parameters every time or cache them? 
        # For simplicity and dynamic reconfigure potential, we'll read them or store them. 
        # Accessing params is cheap enough for 10-100Hz joy.
        
        linear_scale = self.get_parameter('linear_scale').value
        angular_scale = self.get_parameter('angular_scale').value
        axis_linear_idx = self.get_parameter('axis_linear').value
        axis_angular_idx = self.get_parameter('axis_angular').value
        
        # Safety check for indices
        if axis_linear_idx < len(msg.axes):
            twist.linear.x = msg.axes[axis_linear_idx] * linear_scale
        
        if axis_angular_idx < len(msg.axes):
            twist.angular.z = msg.axes[axis_angular_idx] * angular_scale
            
        self.publisher.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = JoyToCmdVel()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
