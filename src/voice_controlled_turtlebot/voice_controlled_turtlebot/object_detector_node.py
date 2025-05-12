import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
import numpy as np

class ObjectDetectorNode(Node):
    def __init__(self):
        super().__init__('object_detector_node')
        self.bridge = CvBridge()
        self.model = YOLO('yolov8n.pt')  # Using YOLOv8 Nano model

        self.detections = []  # List of detected objects
        self.last_frame = None

        self.image_sub = self.create_subscription(
            Image,
            '/oakd/rgb/preview/image_raw',
            self.image_callback,
            10)

        self.command_sub = self.create_subscription(
            String,
            '/voice_command',
            self.command_callback,
            10)

        self.image_pub = self.create_publisher(
            Image,
            '/yolo_image_raw',
            10)

        self.detected_objects_pub = self.create_publisher(
            String,
            '/detected_objects',
            10)

        self.get_logger().info('✅ Object Detector Node Started.')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.last_frame = cv_image
            self.run_detection(cv_image)
        except Exception as e:
            self.get_logger().error(f'Error converting image: {str(e)}')

    def run_detection(self, frame):
        results = self.model.predict(source=frame, conf=0.5, verbose=False)[0]

        detected_labels = []
        annotated_frame = frame.copy()

        for box in results.boxes:
            cls = int(box.cls[0])
            label = self.model.names[cls]
            conf = float(box.conf[0])

            detected_labels.append(label)

            # Draw bounding boxes
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Put label and confidence
            text = f"{label} {conf:.2f}"
            cv2.putText(annotated_frame, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        self.detections = list(set(detected_labels))  # Unique list

        # Publish annotated image
        try:
            yolo_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
            self.image_pub.publish(yolo_msg)
        except Exception as e:
            self.get_logger().error(f'Error publishing YOLO image: {str(e)}')

        # Publish detected objects string
        if self.detections:
            detected_str = ', '.join(self.detections)
            full_message = f"I see: {detected_str}"
        else:
            full_message = "I do not see anything right now."

        detected_msg = String()
        detected_msg.data = full_message
        self.detected_objects_pub.publish(detected_msg)

    def command_callback(self, msg):
        if msg.data == 'what_do_you_see':
            if self.detections:
                detected_str = ', '.join(self.detections)
                self.get_logger().info(f'I see: {detected_str}')
            else:
                self.get_logger().info('I do not see anything right now.')

def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

