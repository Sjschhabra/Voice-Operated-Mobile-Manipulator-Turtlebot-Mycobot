import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from rclpy.action import ActionClient
from irobot_create_msgs.action import Dock, Undock
from irobot_create_msgs.msg import DockStatus
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class MovementControllerNode(Node):
    def __init__(self):
        super().__init__('movement_controller_node')

        self.subscription = self.create_subscription(
            String,
            '/voice_command',
            self.command_callback,
            10)

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/rpi_13/cmd_vel',
            10)

        self.dock_client = ActionClient(self, Dock, '/rpi_13/dock')
        self.undock_client = ActionClient(self, Undock, '/rpi_13/undock')

        self.is_docked = None
        self.create_subscription(DockStatus, '/rpi_13/dock_status', self.dock_status_cb, 10)

        self.docking_in_progress = False
        self.undocking_in_progress = False
        self.last_sent_goal = None  # 'dock', 'undock', or None

        self.image_sub = self.create_subscription(Image, '/oakd/rgb/preview/image_raw', self.image_callback, 10)
        self.bridge = CvBridge()
        self.last_image = None

        self.current_twist = Twist()
        self.moving = False
        self.publish_timer = self.create_timer(0.1, self.publish_movement)

        self.get_logger().info('Movement Controller Node Started.')

    def dock_status_cb(self, msg):
        self.is_docked = msg.is_docked

    def image_callback(self, msg):
        self.last_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    def command_callback(self, msg):
        command = msg.data.lower()

        self.current_twist = Twist()
        self.moving = False

        if command == 'move_forward':
            self.current_twist.linear.x = 0.1
            self.moving = True
        elif command == 'move_backward':
            self.current_twist.linear.x = -0.1
            self.moving = True
        elif command == 'turn_left':
            self.current_twist.angular.z = 0.33
            self.moving = True
        elif command == 'turn_right':
            self.current_twist.angular.z = -0.33
            self.moving = True
        elif command == 'spin':
            self.current_twist.angular.z = 1.0
            self.moving = True
        elif command == 'shake':
            self.start_shake()
        elif command == 'stop':
            self.stop_robot()
        elif command == 'dock':
            self.send_dock_goal()
        elif command == 'undock':
            self.send_undock_goal()
        elif command == 'take_a_picture':
            self.save_snapshot()
        elif command in ["look_for_object", "go_to_object", "return_to_base", "scan"]:
            self.get_logger().info(f"Received non-movement command: {command} (not handled here)")
        else:
            self.get_logger().info(f'Unknown command: {command}')

    def publish_movement(self):
        if self.moving:
            self.cmd_vel_pub.publish(self.current_twist)

    def stop_robot(self):
        self.moving = False
        stop_twist = Twist()
        self.cmd_vel_pub.publish(stop_twist)
        self.get_logger().info('Robot stopped.')

    def start_shake(self):
        self.get_logger().info('Starting SHAKE movement.')
        self.shake_sequence = [(-1.0, 5), (1.0, 5), (-1.0, 5), (1.0, 5)]
        self.shake_index = 0
        self.shake_timer = self.create_timer(0.5, self.shake_step)

    def shake_step(self):
        if self.shake_index < len(self.shake_sequence):
            angular_z, _ = self.shake_sequence[self.shake_index]
            self.current_twist = Twist()
            self.current_twist.angular.z = angular_z
            self.cmd_vel_pub.publish(self.current_twist)
            self.shake_index += 1
        else:
            self.shake_timer.cancel()
            self.stop_robot()

    def send_dock_goal(self):
        if self.last_sent_goal == 'dock':
            self.get_logger().warn("Dock already sent. Ignoring.")
            return
        if self.is_docked is True:
            self.get_logger().warn("Already docked. Not sending dock goal.")
            return
        if self.docking_in_progress:
            self.get_logger().warn("Dock already in progress. Ignoring duplicate.")
            return

        self.get_logger().info('Sending DOCK goal.')
        if not self.dock_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error('Dock action server not available.')
            return

        self.docking_in_progress = True
        self.last_sent_goal = 'dock'
        goal = Dock.Goal()
        future = self.dock_client.send_goal_async(goal)
        future.add_done_callback(self.handle_dock_result)

    def handle_dock_result(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Dock goal rejected.')
            self.docking_in_progress = False
            return

        self.get_logger().info('Dock goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(lambda f: self.finish_docking())

    def finish_docking(self):
        self.get_logger().info('✅ Dock action finished.')
        self.docking_in_progress = False

    def send_undock_goal(self):
        if self.last_sent_goal == 'undock':
            self.get_logger().warn("Undock already sent. Ignoring.")
            return
        if self.is_docked is False:
            self.get_logger().warn("Already undocked. Not sending undock goal.")
            return
        if self.undocking_in_progress:
            self.get_logger().warn("Undock already in progress. Ignoring duplicate.")
            return

        self.get_logger().info('Sending UNDOCK goal.')
        if not self.undock_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error('Undock action server not available.')
            return

        self.undocking_in_progress = True
        self.last_sent_goal = 'undock'
        goal = Undock.Goal()
        future = self.undock_client.send_goal_async(goal)
        future.add_done_callback(self.handle_undock_result)

    def handle_undock_result(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Undock goal rejected.')
            self.undocking_in_progress = False
            return

        self.get_logger().info('Undock goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(lambda f: self.finish_undocking())

    def finish_undocking(self):
        self.get_logger().info('✅ Undock action finished.')
        self.undocking_in_progress = False

    def save_snapshot(self):
        if self.last_image is not None:
            save_path = os.path.expanduser('~/anu_ws/src/snapshot.png')
            cv2.imwrite(save_path, self.last_image)
            self.get_logger().info(f'📸 Snapshot saved to: {save_path}')
        else:
            self.get_logger().warn('No image received yet.')


def main(args=None):
    rclpy.init(args=args)
    node = MovementControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

