import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import os

class MicListenerNode(Node):
    def __init__(self):
        super().__init__('mic_listener_node')

        # Publisher
        self.voice_text_pub = self.create_publisher(String, '/voice_text', 10)

        # Important paths
        self.whispercpp_path = '/home/anushkasatav/whisper.cpp'  # your whisper.cpp folder
        # self.model_file = 'models/ggml-tiny.en.bin'  # inside whisper.cpp/models/
        self.model_file = 'models/ggml-base.en.bin'
        self.temp_wav_file = '/tmp/mic_temp.wav'  # temporary audio storage

        # How often to record+transcribe
        self.timer_period = 5.0  # seconds
        self.timer = self.create_timer(self.timer_period, self.listen_and_transcribe)

        self.get_logger().info('Mic Listener Node Started!')

    def listen_and_transcribe(self):
        self.get_logger().info('🎤 Recording from mic...')

        try:
            # 1. Record audio (3 seconds)
            subprocess.run([
                'arecord',
                '-D', 'plughw:0,0',    # IMPORTANT: correct mic device
                '-f', 'S16_LE',        # 16-bit Little Endian
                '-r', '16000',         # 16kHz sampling
                '-c', '1',             # Mono
                '-t', 'wav',
                '-d', '4',             # record 4 seconds
                self.temp_wav_file
            ], check=True)

            self.get_logger().info('📄 Audio recorded. Transcribing...')

            # 2. Run whisper-cli to transcribe
            result = subprocess.run([
                './whisper-cli',
                '-m', self.model_file,
                '-f', self.temp_wav_file,
                '--output-txt'
            ],
            cwd=self.whispercpp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)

            text_output = result.stdout.strip()

            if text_output:
                self.get_logger().info(f'📝 Whisper output: {text_output}')

                # 3. Publish transcription
                msg = String()
                msg.data = text_output.lower()
                self.voice_text_pub.publish(msg)
                self.get_logger().info(f'📢 Published to /voice_text: {msg.data}')
            else:
                self.get_logger().warn('⚠️ No transcription detected.')

        except Exception as e:
            self.get_logger().error(f'❌ Error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = MicListenerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

