import rclpy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import cv2.aruco as aruco
import numpy as np

bridge = CvBridge()
aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters_create()

def image_callback(msg):
    frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    origin_x = width // 2
    origin_y = height // 2

    # Draw axes (origin at center)
    cv2.line(frame, (origin_x, 0), (origin_x, height), (255, 0, 0), 2)   # Vertical X+
    cv2.line(frame, (0, origin_y), (width, origin_y), (0, 255, 0), 2)    # Horizontal Y+

    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is not None:
        for i, corner in enumerate(corners):
            center = np.mean(corner[0], axis=0)
            cx, cy = int(center[0]), int(center[1])

            # Custom coordinate system
            custom_x = -(cy - origin_y)  # +X is up
            custom_y = -(cx - origin_x)  # +Y is left

            text = f"({custom_x}, {custom_y})"
            cv2.putText(frame, text, (cx + 10, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        aruco.drawDetectedMarkers(frame, corners, ids)

    cv2.imshow("Live ArUco View (Centered Origin)", frame)
    cv2.waitKey(1)

def main():
    rclpy.init()
    node = rclpy.create_node('simple_image_subscriber')
    node.create_subscription(Image, '/oakd/rgb/preview/image_raw', image_callback, 10)
    print("Subscribed to /oakd/rgb/preview/image_raw. Press Ctrl+C to exit.")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
