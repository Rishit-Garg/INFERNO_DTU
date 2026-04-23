#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
import serial
import time
import sys

# GPS Configuration
GPS_PORT = "/dev/ttyUSB0"
GPS_BAUD = 115200

def cleanstr(in_str):
    out_str = "".join([c for c in in_str if c in "0123456789.-"])
    return out_str if out_str else "-1"

def safefloat(in_str):
    try:
        return float(in_str)
    except ValueError:
        return -1.0

class GPSNode(Node):
    def __init__(self):
        super().__init__('gps_publisher_node')
        
        # Declare parameters
        self.declare_parameter('port', GPS_PORT)
        self.declare_parameter('baudrate', GPS_BAUD)
        self.declare_parameter('frame_id', 'gps')
        self.declare_parameter('publish_rate', 5.0)  # Hz
        
        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value
        self.frame_id = self.get_parameter('frame_id').value
        rate = self.get_parameter('publish_rate').value
        
        # Open serial port
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.ser.flush()
            self.get_logger().info(f'GPS connected on {port} at {baudrate} baud')
        except serial.SerialException as e:
            self.get_logger().error(f"Error opening serial port: {e}")
            sys.exit(1)
        
        # Publisher
        self.publisher_ = self.create_publisher(NavSatFix, '/gps/fix', 10)
        
        # Timer to read GPS at specified rate
        self.timer = self.create_timer(1.0 / rate, self.read_and_publish_gps)
        
        self.get_logger().info('GPS Publisher Node started')
    
    def read_gps(self):
        """Read NMEA sentence from GPS"""
        while True:
            try:
                line = self.ser.readline().decode(errors="ignore")
                # L89H uses $GNGGA (multi-constellation), also accept $GPGGA
                if line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                    return line.split(",")
            except Exception as e:
                self.get_logger().warn(f'Error reading GPS: {e}')
                return None
            time.sleep(0.01)
    
    def decimal_degrees(self, raw):
        """Convert NMEA format to decimal degrees"""
        try:
            degrees = int(raw // 100)
            minutes = raw % 100
            return degrees + minutes / 60
        except:
            return raw
    
    def read_and_publish_gps(self):
        """Read GPS data and publish NavSatFix message"""
        gga = self.read_gps()
        
        if gga is None or len(gga) < 10:
            return
        
        # Parse GGA sentence
        try:
            # Time
            time_str = gga[1]
            
            # Latitude
            lat = safefloat(cleanstr(gga[2])) if gga[2] else -1.0
            lat_ns = gga[3] if gga[3] else ""
            
            # Longitude
            lon = safefloat(cleanstr(gga[4])) if gga[4] else -1.0
            lon_ew = gga[5] if gga[5] else ""
            
            # Fix quality
            fix_quality = int(cleanstr(gga[6]))
            
            # Number of satellites
            num_sats = int(cleanstr(gga[7]))
            
            # HDOP (Horizontal Dilution of Precision)
            hdop = safefloat(cleanstr(gga[8])) if len(gga) > 8 and gga[8] else 1.0
            
            # Altitude
            altitude = safefloat(cleanstr(gga[9])) if gga[9] else 0.0
            
            # Convert to decimal degrees
            if lat != -1.0:
                lat = self.decimal_degrees(lat)
                if lat_ns == "S":
                    lat = -lat
            else:
                self.get_logger().warn('Invalid latitude data')
                return
            
            if lon != -1.0:
                lon = self.decimal_degrees(lon)
                if lon_ew == "W":
                    lon = -lon
            else:
                self.get_logger().warn('Invalid longitude data')
                return
            
            # Create and publish NavSatFix message
            msg = NavSatFix()
            
            # Header
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id
            
            # Status
            if fix_quality == 0:
                msg.status.status = NavSatStatus.STATUS_NO_FIX
            elif fix_quality == 1:
                msg.status.status = NavSatStatus.STATUS_FIX
            elif fix_quality >= 2:
                msg.status.status = NavSatStatus.STATUS_GBAS_FIX
            
            msg.status.service = NavSatStatus.SERVICE_GPS
            
            # Position
            msg.latitude = lat
            msg.longitude = lon
            msg.altitude = altitude
            
            # Covariance (estimate based on HDOP)
            # Lower HDOP = better accuracy
            variance = (hdop * 2.0) ** 2  # Rough estimate
            msg.position_covariance = [
                variance, 0.0, 0.0,
                0.0, variance, 0.0,
                0.0, 0.0, variance * 2  # Altitude typically less accurate
            ]
            msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_APPROXIMATED
            
            # Publish
            self.publisher_.publish(msg)
            
            # Log info
            self.get_logger().info(
                f'GPS Fix: {fix_quality} | Sats: {num_sats} | '
                f'Lat: {lat:.6f} | Lon: {lon:.6f} | Alt: {altitude:.2f}m',
                throttle_duration_sec=5.0 
            )
            
        except Exception as e:
            self.get_logger().error(f'Error parsing GPS data: {e}')
    
    def destroy_node(self):
        """Cleanup when shutting down"""
        self.ser.close()
        self.get_logger().info('GPS serial port closed')
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    
    try:
        gps_node = GPSNode()
        rclpy.spin(gps_node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            gps_node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()