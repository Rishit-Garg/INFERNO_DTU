#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import serial
import time


class CmdArmNode(Node):
    def __init__(self):
        super().__init__('cmd_arm')
        #Serial ke params
        self.declare_parameter('serial_port', '/dev/ttyUSB1')
        self.declare_parameter('baud_rate', 115200)

        # Axises
        self.declare_parameter('axis_1', 0)
        self.declare_parameter('axis_2', 1)
        self.declare_parameter('axis_3', 2)

        # Get serial parameters
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value

        #Serial connection
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2)  # Wait for serial connection to stabilize
            self.get_logger().info(f'Serial connected on {port} at {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.ser = None

        # Subscribe to joy topic
        self.subscription = self.create_subscription(
            Joy,
            '/joy',
            self.joy_callback,
            10)

        self.get_logger().info('CmdArm Node Started. Listening on /joy')

    def joy_callback(self, msg):
        if self.ser is None:
            return

        # Get axis indices
        axis_1_idx = self.get_parameter('axis_1').value
        axis_2_idx = self.get_parameter('axis_2').value
        axis_3_idx = self.get_parameter('axis_3').value

        # Extract values with safety checks
        val1 = msg.axes[axis_1_idx] if axis_1_idx < len(msg.axes) else 0.0
        val2 = msg.axes[axis_2_idx] if axis_2_idx < len(msg.axes) else 0.0
        val3 = msg.axes[axis_3_idx] if axis_3_idx < len(msg.axes) else 0.0

        val1_int = int(val1 * 255)
        val2_int = int(val2 * 255)
        val3_int = int(val3 * 255)

        # Format: "<val1 val2 val3>"
        payload = f"<{val1_int} {val2_int} {val3_int}>"

        # Send over serial
        self.ser.write(payload.encode())
        print(f'Sent: {payload}')
        self.get_logger().info(f'Sent: {payload}')

    def destroy_node(self):
        if self.ser is not None:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CmdArmNode()
    print("starting")

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
