
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import socket
import time
ESP32_IP = "192.168.1.101"   # Master Esp 5500 ki ip
ESP32_PORT = 8888

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class CmdUdpNode(Node):
    def __init__(self):
        super().__init__('cmd_udp_node')
        
        # UDP Setup
        self.udp_ip = ESP32_IP
        self.udp_port = ESP32_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Subscription
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.listener_callback,
            10)
        self.subscription  
        
        self.get_logger().info(f'UDP Sender Node Started. Target: {self.udp_ip}:{self.udp_port}')
        
    def listener_callback(self, msg):
        # wl aur wr ki calculation
        R=0.14
        L=0.62
        wl=-(msg.linear.x -(msg.angular.z *L))/R*50
        wr=(msg.linear.x +(msg.angular.z *L))/R*50
        

        data_str=f"<{wl:.2f} {wl:.2f} {wl:.2f} {wr:.2f} {wr:.2f} {wr:.2f}>"
        # Sending via UDP
        self.sock.sendto(data_str.encode(), (self.udp_ip, self.udp_port))
        self.get_logger().info(f'Sent: "{data_str}"')
        time.sleep(1)

def main(args=None):
    rclpy.init(args=args)
    cmd_udp_node = CmdUdpNode()
    
    try:
        rclpy.spin(cmd_udp_node)
    except KeyboardInterrupt:
        pass
    finally:
        cmd_udp_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
