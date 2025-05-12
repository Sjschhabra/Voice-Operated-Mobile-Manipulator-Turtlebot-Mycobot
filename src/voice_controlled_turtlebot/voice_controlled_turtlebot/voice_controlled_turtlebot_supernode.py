import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import pyaudio
import wave
import whisper

class VoiceControlledTurtlebotNode(Node):
    def __init__(self):  # ✅ fixed: double underscores
        super().__init__('voice_controlled_turtlebot_node')  # ✅ fixed: correct super()

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.voice_text_pub = self.create_publisher(String, '/voice_text', 10)

        # Microphone settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 4
        self.output_filename = 'temp.wav'

        self.audio = pyaudio.PyAudio()

        # Whisper model
        self.model = whisper.load_model("small")

        # Keywords to detect
        self.keywords = ["forward", "backward", "left", "right", "stop", "start", "slow", "emergency stop"]

        # Start timer
        self.timer = self.create_timer(5.0, self.main_loop)

        self.get_logger().info('Voice Controlled TurtleBot Node Started!')

    def main_loop(self):
        self.record_audio()
        text = self.transcribe_audio()
        if text:
            commands = self.extract_commands(text)
            if commands:
                self.publish_movement(commands)

    def record_audio(self):
        self.get_logger().info('Recording audio...')
        stream = self.audio.open(format=self.format, channels=self.channels,
                                 rate=self.rate, input=True,
                                 frames_per_buffer=self.chunk)

        frames = []

        for _ in range(0, int(self.rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        wf = wave.open(self.output_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        self.get_logger().info('Audio recorded.')

    def transcribe_audio(self):
        self.get_logger().info('Transcribing audio...')
        try:
            result = self.model.transcribe(self.output_filename)
            text = result['text'].strip().lower()
            self.get_logger().info(f"Transcribed Text: {text}")

            # Publish full text to /voice_text
            msg = String()
            msg.data = text
            self.voice_text_pub.publish(msg)
            self.get_logger().info(f"Published voice text: {text}")

            return text
        except Exception as e:
            self.get_logger().error(f"Failed to transcribe: {e}")
            return None

    def extract_commands(self, text):
        found_commands = []
        for keyword in self.keywords:
            if keyword in text:
                found_commands.append(keyword)

        if found_commands:
            self.get_logger().info(f"Parsed Commands: {found_commands}")
            return found_commands
        else:
            self.get_logger().info('No valid command found.')
            return None

    def publish_movement(self, commands):
        twist = Twist()

        if "emergency stop" in commands:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.get_logger().warn('EMERGENCY STOP triggered!')
        else:
            if "forward" in commands:
                twist.linear.x = 0.2
            if "backward" in commands:
                twist.linear.x = -0.2
            if "left" in commands:
                twist.angular.z = 0.5
            if "right" in commands:
                twist.angular.z = -0.5
            if "stop" in commands:
                twist.linear.x = 0.0
                twist.angular.z = 0.0
            if "slow" in commands:
                twist.linear.x = 0.05

        self.cmd_vel_pub.publish(twist)
        self.get_logger().info('Published movement command.')

def main(args=None):
    rclpy.init(args=args)
    node = VoiceControlledTurtlebotNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':  # ✅ fixed
    main()

