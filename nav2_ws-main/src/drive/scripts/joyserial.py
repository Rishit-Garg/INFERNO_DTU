import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import serial

SERIAL_PORT = "/dev/ttyUSB1"
BAUD_RATE = 115200
SCALE = 200

class JoySerialNode(Node):
    def __init__(self):
        super().__init__('joy_serial')
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.get_logger().info(f'Serial port opened: {SERIAL_PORT}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial: {e}')
            raise
            
        self.subscription = self.create_subscription(
            Joy,
            '/j0',
            self.joy_callback,
            10
        )

    def joy_callback(self, msg):
        if len(msg.axes) < 2:
            return
        
        # Forward & skid
        fwd = msg.axes[1] * SCALE
        skid = msg.axes[0] * SCALE
        
        wl = fwd - skid
        wr = fwd + skid
        
        # 6-wheel skid rover
        values = [wl, wl, wl, wr, wr, wr]
        
        # Scale index 1 and 4
        values[1] *= 0.46
        values[4] *= 0.46
        
        # **FIX: Convert to integers and clamp to int16_t range**
        int_values = [max(-32767, min(32767, int(v))) for v in values]
        
        # **FIX: Format as integers**
        payload = "<" + " ".join(str(v) for v in int_values) + ">"
        
        try:
            self.ser.write(payload.encode())
            self.get_logger().debug(f'Sent: {payload.strip()}')
        except serial.SerialException as e:
            self.get_logger().error(f'Write failed: {e}')

    def destroy_node(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = JoySerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
