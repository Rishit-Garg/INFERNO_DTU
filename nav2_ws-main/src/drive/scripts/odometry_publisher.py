#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import JointState
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Quaternion
from tf2_ros import TransformBroadcaster
import math

class OdometryPublisher(Node):
    def __init__(self):
        super().__init__('odometry_publisher')
        
        # DON'T declare use_sim_time - passed from launch file
        
        # Publishers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Subscriber to joint states
        self.joint_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        # Robot parameters
        self.wheel_radius = 0.1125
        self.wheel_base = 0.54
        
        # Odometry state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        # Previous wheel positions
        self.prev_left_pos = 0.0
        self.prev_right_pos = 0.0
        self.prev_time = None
        
        # First callback flag
        self.first_callback = True
        
        # Covariance matrices (36 elements each)
        self.pose_covariance = [
            0.001, 0.0,   0.0,   0.0,   0.0,   0.0,
            0.0,   0.001, 0.0,   0.0,   0.0,   0.0,
            0.0,   0.0,   1e6,   0.0,   0.0,   0.0,
            0.0,   0.0,   0.0,   1e6,   0.0,   0.0,
            0.0,   0.0,   0.0,   0.0,   1e6,   0.0,
            0.0,   0.0,   0.0,   0.0,   0.0,   0.03
        ]
        
        self.twist_covariance = [
            0.001, 0.0,   0.0,   0.0,   0.0,   0.0,
            0.0,   0.001, 0.0,   0.0,   0.0,   0.0,
            0.0,   0.0,   1e6,   0.0,   0.0,   0.0,
            0.0,   0.0,   0.0,   1e6,   0.0,   0.0,
            0.0,   0.0,   0.0,   0.0,   1e6,   0.0,
            0.0,   0.0,   0.0,   0.0,   0.0,   0.03
        ]
        
        self.get_logger().info('✅ OdometryPublisher initialized and running.')
    
    def joint_state_callback(self, msg):
        try:
            # Use timestamp from joint_states message
            if msg.header.stamp.sec == 0 and msg.header.stamp.nanosec == 0:
                current_time = self.get_clock().now()
                self.get_logger().warn('⚠️  Joint states has no timestamp', 
                                      throttle_duration_sec=5.0)
            else:
                current_time = Time.from_msg(msg.header.stamp)
            
            # Find wheel joint indices
            wheel_indices = {'left': [], 'right': []}
            
            left_wheels = ['joint_wheel_4', 'joint_wheel_5', 'joint_wheel_6']
            right_wheels = ['joint_wheel_1', 'joint_wheel_2', 'joint_wheel_3']
            
            for i, name in enumerate(msg.name):
                if name in left_wheels:
                    wheel_indices['left'].append(i)
                elif name in right_wheels:
                    wheel_indices['right'].append(i)
            
            if not wheel_indices['left'] or not wheel_indices['right']:
                self.get_logger().warn('⚠️  Wheel joints not found', 
                                      throttle_duration_sec=2.0)
                return
            
            # Calculate average wheel positions
            left_pos = sum(msg.position[i] for i in wheel_indices['left']) / len(wheel_indices['left'])
            right_pos = sum(msg.position[i] for i in wheel_indices['right']) / len(wheel_indices['right'])
            
            # Initialize on first callback
            if self.first_callback or self.prev_time is None:
                self.prev_left_pos = left_pos
                self.prev_right_pos = right_pos
                self.prev_time = current_time
                self.first_callback = False
                self.get_logger().info('📊 Odometry started.')
                return
            
            # Calculate time delta
            dt = (current_time.nanoseconds - self.prev_time.nanoseconds) / 1e9
            if dt <= 0 or dt > 1.0:
                self.get_logger().warn(f'⚠️  Invalid dt: {dt:.3f}s', 
                                      throttle_duration_sec=2.0)
                self.prev_time = current_time
                return
            
            # Calculate wheel deltas
            delta_left = left_pos - self.prev_left_pos
            delta_right = right_pos - self.prev_right_pos
            
            # Calculate distances
            dist_left = delta_left * self.wheel_radius
            dist_right = delta_right * self.wheel_radius
            
            # Calculate robot displacement
            dist_center = (dist_left + dist_right) / 2.0
            delta_theta = (dist_right - dist_left) / self.wheel_base
            
            # Update pose
            self.x += dist_center * math.cos(self.theta + delta_theta / 2.0)
            self.y += dist_center * math.sin(self.theta + delta_theta / 2.0)
            self.theta += delta_theta
            
            # Normalize theta
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
            
            # Calculate velocities
            linear_vel = dist_center / dt
            angular_vel = delta_theta / dt
            
            # Create odometry message
            odom = Odometry()
            odom.header.stamp = current_time.to_msg()
            odom.header.frame_id = 'odom'
            odom.child_frame_id = 'base_link'
            
            # Set position
            odom.pose.pose.position.x = self.x
            odom.pose.pose.position.y = self.y
            odom.pose.pose.position.z = 0.0
            
            # Set orientation
            odom.pose.pose.orientation = self.euler_to_quaternion(0, 0, self.theta)
            odom.pose.covariance = self.pose_covariance
            
            # Set velocities
            odom.twist.twist.linear.x = linear_vel
            odom.twist.twist.linear.y = 0.0
            odom.twist.twist.angular.z = angular_vel
            odom.twist.covariance = self.twist_covariance
            
            # Publish
            self.odom_pub.publish(odom)
            self.publish_tf(current_time, odom.pose.pose.orientation)
            
            # Update previous values
            self.prev_left_pos = left_pos
            self.prev_right_pos = right_pos
            self.prev_time = current_time
            
        except Exception as e:
            self.get_logger().error(f'❌ Error: {str(e)}')
    
    def euler_to_quaternion(self, roll, pitch, yaw):
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        
        q = Quaternion()
        q.x = qx
        q.y = qy
        q.z = qz
        q.w = qw
        return q
    
    def publish_tf(self, current_time, orientation):
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation = orientation
        
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = OdometryPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()