import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from pymycobot import MyCobot
import time
import sympy as sp


def get_link3endsimple(Kx_val, Ky_val, Kz_val, t4_val_deg, t5_val_deg):
    Px, Py, Pz, t4, t5, t6 = sp.symbols('Px Py Pz t4 t5 t6')
    t4_val = t4_val_deg * sp.pi / 180
    t5_val = t5_val_deg * sp.pi / 180
    t6_val = 0

    H14 = sp.Matrix([
        [Px / sp.sqrt(Px**2 + Py**2), 0, Py / sp.sqrt(Px**2 + Py**2), Px],
        [Py / sp.sqrt(Px**2 + Py**2), 0, -Px / sp.sqrt(Px**2 + Py**2), Py],
        [0, 1, 0, Pz],
        [0, 0, 0, 1]
    ])

    H45 = sp.Matrix([
        [0, sp.sin(t4), sp.cos(t4), 0],
        [0, -sp.cos(t4), sp.sin(t4), 0],
        [1, 0, 0, 6639/100],
        [0, 0, 0, 1]
    ])

    H56 = sp.Matrix([
        [0, sp.cos(t5), -sp.sin(t5), 0],
        [0, sp.sin(t5), sp.cos(t5), 0],
        [1, 0, 0, 3659/50],
        [0, 0, 0, 1]
    ])

    H6e = sp.Matrix([
        [sp.cos(t6), -sp.sin(t6), 0, 0],
        [sp.sin(t6), sp.cos(t6), 0, 0],
        [0, 0, 1, 218/5],
        [0, 0, 0, 1]
    ])

    H45 = H45.subs({t4: t4_val})
    H56 = H56.subs({t5: t5_val})
    H6e = H6e.subs({t6: t6_val})

    H_total = H14 * H45 * H56 * H6e

    translation_vector = H_total[0:3, 3]
    Sx = translation_vector[0]
    Sy = translation_vector[1]
    Sz = translation_vector[2]

    eq1 = sp.Eq(Sx, Kx_val)
    eq2 = sp.Eq(Sy, Ky_val)
    eq3 = sp.Eq(Sz, Kz_val)

    initial_guess = (50, 50, 50)

    solution = sp.nsolve([eq1, eq2, eq3], (Px, Py, Pz), initial_guess)
    return round(float(solution[0]), 2), round(float(solution[1]), 2), round(float(solution[2]), 2)


def get_inverse(x, y, z, t4_val=90, t5_val=0):
    Px, Py, Pz = get_link3endsimple(x, y, z, t4_val, t5_val)

    t1 = np.arctan2(Py, Px) * 180 / np.pi
    dz = Pz - 131.56
    base = np.sqrt(Px**2 + Py**2 + (dz)**2)

    base2 = np.sqrt(Px**2 + Py**2)
    extra_t2 = np.degrees(np.arctan2(dz, base2))

    side1 = 110.4
    side2 = 96.0
    theta1 = np.arccos((base**2 + side1**2 - side2**2) / (2 * base * side1)) 
    theta2 = np.arccos((base**2 + side2**2 - side1**2) / (2 * base * side2))
    alpha1 = np.degrees(theta1)
    alpha2 = np.degrees(theta2)

    theta_deg = np.degrees((np.pi - theta1 - theta2))

    angles = [
        t1,
        -1 * (90 - (alpha1 + extra_t2)),
        -180 + theta_deg,
        1 * (1 * (alpha2 - extra_t2) + t4_val),
        -t1,
        50
    ]

    for i in range(len(angles)):
        if angles[i] == 360 or angles[i] == -360:
            angles[i] = 0

    if any(np.isnan(angle) for angle in angles): print("NAAAAAAAAAAAAAAAAAANNNNNNNNN")

    return angles


class RobotArmListener(Node):
    def __init__(self):
        super().__init__('robot_arm_listener')
        self.subscription = self.create_subscription(
            Image,
            '/camera_image_raw',
            self.listener_callback,
            10
        )
        self.subscription  
        self.bridge = CvBridge()
        self.mc = MyCobot("COM3")
        self.get_logger().info("Robot Arm Listener Node Started")

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.detect_aruco_marker(cv_image)

    def detect_aruco_marker(self, image):
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters_create()

        corners, ids, rejected_img_points = cv2.aruco.detectMarkers(image, aruco_dict, parameters=parameters)

        if ids is not None:
            for i in range(len(ids)):
                center = np.mean(corners[i][0], axis=0)
                px, py = center[0], center[1]

                self.get_logger().info(f"Detected ArUco Marker: ID={ids[i]}, Pixel Coordinates: [px={px}, py={py}]")

                c = 0.1
                Pz = 10 + c * px
                Py = 20 + c * py

                ik_angles = get_inverse(250, Py, Pz)

                self.mc.send_angles(ik_angles, 50)
                time.sleep(1)
                print(self.mc.get_coords())
                self.get_logger().info("Angles sent to the robot arm!")


def main(args=None):
    rclpy.init(args=args)
    robot_arm_listener = RobotArmListener()
    rclpy.spin(robot_arm_listener)
    robot_arm_listener.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    while True:
        main()
        time.sleep(10)
