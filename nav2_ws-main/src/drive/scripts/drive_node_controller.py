#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import pydualsense
import time

class DualSenseController(Node):
    def __init__(self):
        super().__init__('dualsense_controller')
        
        # Initialize DualSense
        self.ds = pydualsense.pydualsense()
        try:
            self.ds.init()
            self.get_logger().info("DualSense controller initialized successfully")
            self.setup_resistance()
        except Exception as e:
            self.get_logger().error(f"Failed to initialize DualSense controller: {e}")
            self.ds = None

        # Subscribe to Joy topic
        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10)
        self.subscription  # prevent unused variable warning

    def setup_resistance(self):
        """Sets both triggers to rigid/resistance mode."""
        if self.ds is None:
            return
            
        try:
            # Set Left Trigger to Resistance
            self.ds.triggerL.setMode(pydualsense.TriggerModes.Rigid)
            self.ds.triggerL.setForce(1, 0)   # Start position
            self.ds.triggerL.setForce(2, 255) # Max force
            
            # Set Right Trigger to Resistance
            self.ds.triggerR.setMode(pydualsense.TriggerModes.Rigid)
            self.ds.triggerR.setForce(1, 0)   # Start position
            self.ds.triggerR.setForce(2, 255) # Max force
            
            self.get_logger().info("Triggers set to resistance mode")
        except Exception as e:
            self.get_logger().error(f"Failed to set resistance: {e}")

    def joy_callback(self, msg):
        if self.ds is None:
            return

        try:
            # Left Trigger (Axis 4)
            if len(msg.axes) > 4:
                l_val = msg.axes[4]
                # Map 1.0 (released) to 0.0, -1.0 (pressed) to 1.0
                l_norm = (1.0 - l_val) / 2.0
                l_norm = max(0.0, min(1.0, l_norm)) # Clamp
                self.ds.setLeftMotor(int(l_norm * 255))

            # Right Trigger (Axis 5)
            if len(msg.axes) > 5:
                r_val = msg.axes[5]
                # Map 1.0 (released) to 0.0, -1.0 (pressed) to 1.0
                r_norm = (1.0 - r_val) / 2.0
                r_norm = max(0.0, min(1.0, r_norm)) # Clamp
                self.ds.setRightMotor(int(r_norm * 255))

        except Exception as e:
            self.get_logger().error(f"Error in joy callback: {e}")

    def close(self):
        if self.ds:
            self.ds.close()

def main(args=None):
    rclpy.init(args=args)
    controller = DualSenseController()

    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()
        controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
