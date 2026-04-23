#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import pygame
import time

class MultiJoyPublisher(Node):
    def __init__(self):
        super().__init__('multi_joy_publisher')

        # ROS publishers
        self.pub_joy0 = self.create_publisher(Joy, 'joy0', 10)
        self.pub_joy2 = self.create_publisher(Joy, 'joy2', 10)

        # Init pygame
        pygame.init()
        pygame.joystick.init()

        self.get_logger().info(
            f"Number of joysticks detected: {pygame.joystick.get_count()}"
        )

        if pygame.joystick.get_count() < 2:
            self.get_logger().error("Less than 2 joysticks detected!")
            return

        # Initialize joysticks
        self.joy0 = pygame.joystick.Joystick(0)
        self.joy2 = pygame.joystick.Joystick(1)

        self.joy0.init()
        self.joy2.init()

        self.get_logger().info(f"Joystick 0: {self.joy0.get_name()}")
        self.get_logger().info(f"Joystick 2: {self.joy2.get_name()}")

        # Timer (50 Hz)
        self.timer = self.create_timer(0.02, self.publish_joys)

    def read_joystick(self, joystick):
        axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
        return axes, buttons

    def publish_joys(self):
        pygame.event.pump()

        # Joystick 1 → joy0
        axes0, buttons0 = self.read_joystick(self.joy0)
        msg0 = Joy()
        msg0.header.stamp = self.get_clock().now().to_msg()
        msg0.axes = axes0
        msg0.buttons = buttons0
        self.pub_joy0.publish(msg0)

        # Joystick 2 → joy2
        axes2, buttons2 = self.read_joystick(self.joy2)
        msg2 = Joy()
        msg2.header.stamp = self.get_clock().now().to_msg()
        msg2.axes = axes2
        msg2.buttons = buttons2
        self.pub_joy2.publish(msg2)

def main(args=None):
    rclpy.init(args=args)
    node = MultiJoyPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
