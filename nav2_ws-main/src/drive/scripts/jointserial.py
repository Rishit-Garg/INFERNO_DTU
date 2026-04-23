#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import serial
import time


class WheelVelSerialNode(Node):
    def __init__(self):
        super().__init__('wheel_vel_serial')

        # === PARAMETERS ===
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('left_joint', 'drivewhl_l_joint')
        self.declare_parameter('right_joint', 'drivewhl_r_joint')
        self.declare_parameter('publish_rate', 1.0)  # Hz (new parameter)

        self.serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        self.baud_rate   = self.get_parameter('baud_rate').get_parameter_value().integer_value
        self.left_joint  = self.get_parameter('left_joint').get_parameter_value().string_value
        self.right_joint = self.get_parameter('right_joint').get_parameter_value().string_value
        self.publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value

        # === SERIAL SETUP ===
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=10)
            time.sleep(0.1)  # Wait for Arduino/etc. to reset
            self.get_logger().info(f"Serial port {self.serial_port} opened at {self.baud_rate} baud")
        except serial.SerialException as e:
            self.get_logger().fatal(f"Failed to open serial port: {e}")
            raise

        # === STATE VARIABLES ===
        self.v_l = 0.0
        self.v_r = 0.0
        self.last_update_time = self.get_clock().now()

        # === SUBSCRIPTION ===
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )

        # === TIMER ===
        timer_period = 0.1 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(
            f"Node ready. Sending '<L:x R:y>' to {self.serial_port} at {self.publish_rate:.1f} Hz\n"
            f"  Left joint : {self.left_joint}\n"
            f"  Right joint: {self.right_joint}"
        )

    # ---------------------------------------------------------------
    def joint_state_callback(self, msg: JointState):
        found_l = False
        found_r = False

        for i, name in enumerate(msg.name):
            if name == self.left_joint and i < len(msg.velocity):
                self.v_l = msg.velocity[i]
                found_l = True
            elif name == self.right_joint and i < len(msg.velocity):
                self.v_r = msg.velocity[i]
                found_r = True

        if not (found_l and found_r):
            missing = []
            if not found_l:
                missing.append(self.left_joint)
            if not found_r:
                missing.append(self.right_joint)
            self.get_logger().warn_once(f"Missing joints: {missing}")

        self.last_update_time = self.get_clock().now()


    # ---------------------------------------------------------------
    def timer_callback(self):
        # Send latest velocities at fixed interval
        print("writing")

        line = f"<{self.v_l:.2f} {self.v_r:.2f}>\n"
        print(line)
        try:
            self.ser.write(line.encode('utf-8'))
            self.get_logger().debug(f"Sent: {line.strip()}")
        except serial.SerialException as e:
            self.get_logger().error(f"Serial write failed: {e}")
        print("writed")

    # ---------------------------------------------------------------
    def destroy_node(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            self.get_logger().info("Serial port closed.")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = WheelVelSerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
