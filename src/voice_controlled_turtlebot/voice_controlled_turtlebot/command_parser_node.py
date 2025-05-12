import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class CommandParserNode(Node):
    def __init__(self):
        super().__init__('command_parser_node')

        self.subscription = self.create_subscription(
            String,
            '/voice_text',
            self.voice_callback,
            10)

        self.command_pub = self.create_publisher(
            String,
            '/voice_command',
            10)

        self.valid_commands = [
            'move_forward', 'move_backward', 'turn_left', 'turn_right',
            'stop', 'look_for_object', 'go_to_object', 'return_to_base',
            'scan', 'repeat', 'dock', 'undock', 'spin', 'shake', 'take_a_picture',
            'home_position', 'list_position', 'relax_position', 'wave_emote', 'grasp'
        ]

        self.current_command = None
        self.publish_timer = None
        self.elapsed_time = 0.0

        self.get_logger().info('Command Parser Node Started.')

    def voice_callback(self, msg):
        text = msg.data.lower()
        self.get_logger().info(f'Voice text received: {text}')

        found_command = None

        #for keyword in self.valid_commands:
            #if keyword.replace('_', ' ') in text:
                #found_command = keyword
                #break
        for keyword in sorted(self.valid_commands, key=lambda k: -len(k)):
            if keyword.replace('_', ' ') in text:
                found_command = keyword
                break


        if found_command:
            self.get_logger().info(f'Parsed Command: {found_command}')
            self.start_command_publish(found_command)
        else:
            self.get_logger().info('No valid command detected.')

    def start_command_publish(self, command):
        self.current_command = command
        self.elapsed_time = 0.0

        if self.publish_timer:
            self.publish_timer.cancel()

        # Publish every 0.5 sec (2Hz)
        self.publish_timer = self.create_timer(0.5, self.publish_command)

    def publish_command(self):
        if self.elapsed_time >= 5.0:
            # Stop after 5 seconds
            self.get_logger().info('Finished publishing command.')
            if self.publish_timer:
                self.publish_timer.cancel()
                self.publish_timer = None
            self.current_command = None
            return

        if self.current_command:
            msg = String()
            msg.data = self.current_command
            self.command_pub.publish(msg)
            self.get_logger().info(f'Published command: {self.current_command}')

        self.elapsed_time += 0.5

def main(args=None):
    rclpy.init(args=args)
    node = CommandParserNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

