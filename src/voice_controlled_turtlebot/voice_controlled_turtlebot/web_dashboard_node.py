
import sys
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, Imu, LaserScan, BatteryState
from diagnostic_msgs.msg import DiagnosticArray
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, QGroupBox, QPushButton, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from irobot_create_msgs.msg import DockStatus

PLACEHOLDER_IMAGE_PATH = '/home/anushkasatav/anu_ws/src/voice_controlled_turtlebot/1.png'

class IMUPlotCanvas(FigureCanvas):
    def __init__(self, parent=None, title='IMU Data', height=2):
        fig = Figure(figsize=(4, height), dpi=100, facecolor='#0a1a2f')
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.x_data, self.y_data, self.z_data = [], [], []
        self.title = title

    def update_plot(self, x, y, z):
        self.x_data.append(x)
        self.y_data.append(y)
        self.z_data.append(z)
        if len(self.x_data) > 50:
            self.x_data.pop(0); self.y_data.pop(0); self.z_data.pop(0)
        self.ax.clear()
        self.ax.set_facecolor('#0a1a2f')
        self.ax.set_title(self.title, color='white', fontsize=8)
        self.ax.plot(self.x_data, 'r-', label='X')
        self.ax.plot(self.y_data, 'g-', label='Y')
        self.ax.plot(self.z_data, 'b-', label='Z')
        self.ax.tick_params(colors='white', labelsize=6)
        self.ax.legend(loc='upper right', fontsize=6)
        self.draw()

class LidarCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.points = []
        self.setMinimumSize(550, 400)

    def update_points(self, points):
        self.points = points
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(20, 20, 20))
        center_x, center_y = self.width() // 2, self.height() // 2
        for x, y in self.points:
            dist = np.sqrt(x**2 + y**2)
            color = QColor(255, 0, 0) if dist < 20 else QColor(0, 255, 0)
            painter.setPen(QPen(color, 2))
            painter.drawPoint(int(center_x + x), int(center_y + y))
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawEllipse(center_x - 2, center_y - 2, 4, 4)

class ControlButton(QPushButton):
    def __init__(self, label, command, ros_node):
        super().__init__(label)
        self.command = command
        self.ros_node = ros_node
        self.setStyleSheet("background-color: #1c2e44; color: white; font-weight: bold; font-size: 10pt;")
        self.setFixedHeight(30)
        self.clicked.connect(self.send_command)
        shades = ["#1f3c5c", "#224869"]
        color = shades[hash(label) % len(shades)]
        self.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; font-size: 10pt;")


    def send_command(self):
        msg = String()
        msg.data = self.command
        self.ros_node.voice_text_pub.publish(msg)
        self.ros_node.voice_text = msg.data

class TurtlebotGUI(QMainWindow):
    def __init__(self, ros_node):
        super().__init__()
        self.setWindowTitle("🧠 TurtleBot4 + MyCobot Control Panel")
        #self.setStyleSheet("background-color: #0a1a2f; color: white;")
        self.setStyleSheet("background-color: #060e1a; color: white;")
        self.setGeometry(100, 100, 1800, 950)
        self.ros_node = ros_node
        self.bridge = CvBridge()
        self.placeholder_pixmap = QPixmap(PLACEHOLDER_IMAGE_PATH)
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(50)

    def labeled_box(self, title, widget):
        box = QGroupBox(title)
        box.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; color: white; border: 1px solid #555; margin-top: 5px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 2 8px; }")
        layout = QVBoxLayout()
        layout.addWidget(widget)
        box.setLayout(layout)
        return box

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        status_layout = QHBoxLayout()
        self.battery_label = QLabel("Battery: N/A%")
        self.temp_label = QLabel("Temp: N/A°C")
        self.cpu_label = QLabel("CPU: N/A%")
        self.dock_label = QLabel("Dock: Unknown")


        #for label in [self.battery_label, self.temp_label, self.cpu_label]:
        #    label.setStyleSheet("font-size: 10pt; color: white; padding: 5px;")
        for label in [self.battery_label, self.temp_label, self.cpu_label, self.dock_label]:
            label.setStyleSheet("font-size: 10pt; color: white; padding: 5px;")
        status_layout.addWidget(self.dock_label)

        status_layout.addWidget(self.battery_label)
        status_layout.addWidget(self.temp_label)
        status_layout.addWidget(self.cpu_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        content_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        self.camera_label = QLabel(); self.camera_label.setAlignment(Qt.AlignCenter)
        self.yolo_label = QLabel(); self.yolo_label.setAlignment(Qt.AlignCenter)
        #self.placeholder_label = QLabel(); self.placeholder_label.setPixmap(self.placeholder_pixmap)
        arm_btn_layout = QVBoxLayout()
        for label in ["🏠 Home Position", "📋 List Position", "🛌 Relax Position", "👋 Wave Emote", "🤏 Grasp"]:
            b = QPushButton(label)
            b.setStyleSheet("background-color: #1a2d44; color: white; font-weight: bold; margin: 2px")
            b.setFixedHeight(28)
            arm_btn_layout.addWidget(b)
        arm_box = QWidget(); arm_box.setLayout(arm_btn_layout)
        left_layout.addWidget(self.labeled_box("🤖 Robotic Arm Controls", arm_box))
        arm_btn_layout = QVBoxLayout()
        for label in ["🏠 Home Position", "📋 List Position", "🛌 Relax Position", "👋 Wave Emote", "🤏 Grasp"]:
            b = QPushButton(label)
            b.setStyleSheet("background-color: #1a2d44; color: white; font-weight: bold; margin: 2px")
            b.setFixedHeight(28)
            arm_btn_layout.addWidget(b)
        #arm_box = QWidget(); arm_box.setLayout(arm_btn_layout)
        #left_layout.addWidget(self.labeled_box("🤖 Robotic Arm Controls", arm_box))

        left_layout.addWidget(self.labeled_box("📷 RGB Camera Feed", self.camera_label))
        left_layout.addWidget(self.labeled_box("🎯 YOLOv8 Detection", self.yolo_label))
        #left_layout.addWidget(self.labeled_box("🤖 Robotic Arm Control", self.placeholder_label))

        center_layout = QVBoxLayout()
        self.voice_text = QTextEdit(); self.voice_text.setReadOnly(True); self.voice_text.setFixedHeight(80)
        self.voice_cmd = QTextEdit(); self.voice_cmd.setReadOnly(True); self.voice_cmd.setFixedHeight(80)
        self.object_info = QTextEdit(); self.object_info.setReadOnly(True); self.object_info.setFixedHeight(80)
        self.lidar_widget = LidarCanvas()
        center_layout.addWidget(self.labeled_box("🗣️ Voice Input", self.voice_text))
        center_layout.addWidget(self.labeled_box("🔄 Parsed Command", self.voice_cmd))
        center_layout.addWidget(self.labeled_box("📦 Detected Objects", self.object_info))
        center_layout.addWidget(self.labeled_box("📡 LIDAR Mapping", self.lidar_widget))

        right_layout = QVBoxLayout()
        self.linear_plot = IMUPlotCanvas(title="📈 Linear Acceleration (X, Y, Z)", height=1.5)
        self.angular_plot = IMUPlotCanvas(title="📉 Angular Velocity (X, Y, Z)", height=1.5)
        self.imu_status = QTextEdit(); self.imu_status.setReadOnly(True); self.imu_status.setFixedHeight(40)
        right_layout.addWidget(self.linear_plot)
        right_layout.addWidget(self.angular_plot)
        right_layout.addWidget(self.labeled_box("🧭 IMU Orientation Analysis", self.imu_status))

        btn_layout = QHBoxLayout()
        cmds = ["move forward", "move backward", "turn left", "turn right", "stop",
                "look for object", "go to object", "return to base", "scan", "repeat",
                "dock", "undock", "spin", "shake", "take a picture"]
        col1 = QVBoxLayout(); col2 = QVBoxLayout()
        for i, c in enumerate(cmds):
            btn = ControlButton(c.title(), c, self.ros_node)
            (col1 if i % 2 == 0 else col2).addWidget(btn)
        btn_layout.addLayout(col1); btn_layout.addLayout(col2)
        command_box = QWidget(); command_box.setLayout(btn_layout)
        scroll = QScrollArea(); scroll.setWidget(command_box); scroll.setWidgetResizable(True); scroll.setFixedHeight(350)
        right_layout.addWidget(self.labeled_box("🎮 Voice + GUI Commands", scroll))

        content_layout.addLayout(left_layout, 2)
        content_layout.addLayout(center_layout, 3)
        content_layout.addLayout(right_layout, 3)

        main_layout.addLayout(content_layout)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def update_gui(self):
        rclpy.spin_once(self.ros_node, timeout_sec=0)
        if self.ros_node.camera_image is not None:
            self.display_image(self.camera_label, self.ros_node.camera_image)
        if self.ros_node.yolo_image is not None:
            self.display_image(self.yolo_label, self.ros_node.yolo_image)
        self.voice_text.setText(self.ros_node.voice_text)
        self.voice_cmd.setText(self.ros_node.voice_command)
        self.object_info.setText(self.ros_node.detected_objects)
        if self.ros_node.linear_imu:
            x, y, z = self.ros_node.linear_imu
            self.linear_plot.update_plot(x, y, z)
            self.imu_status.setText(self.analyze_imu(x, y))
        if self.ros_node.angular_imu:
            self.angular_plot.update_plot(*self.ros_node.angular_imu)
        if self.ros_node.lidar_points:
            self.lidar_widget.update_points(self.ros_node.lidar_points)
        if self.ros_node.battery_percentage is not None:
            self.battery_label.setText(f"Battery: {self.ros_node.battery_percentage:.1%}")
        if self.ros_node.temperature is not None:
            self.temp_label.setText(f"Temp: {self.ros_node.temperature:.1f}°C")
        if self.ros_node.cpu_usage is not None:
            self.cpu_label.setText(f"CPU: {self.ros_node.cpu_usage:.1%}")
        if self.ros_node.is_docked is not None:
            dock_status = '✅ Docked' if self.ros_node.is_docked else '❌ Undocked'
            self.dock_label.setText(f'Dock: {dock_status}')

    def analyze_imu(self, ax, ay):
        if ax > 0.05:
            return "⚠️ Tilted Forward"
        elif ax < -0.05:
            return "⚠️ Tilted Backward"
        elif ay > 0.05:
            return "⚠️ Tilted Right"
        elif ay < -0.05:
            return "⚠️ Tilted Left"
        return "✅ Stable Orientation"

    def display_image(self, label, img):
        qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_BGR888)
        pix = QPixmap.fromImage(qimg)
        label.setPixmap(pix.scaled(label.size(), Qt.KeepAspectRatio))

class TurtlebotNode(Node):
    def __init__(self):
        super().__init__('turtlebot_gui_node')
        self.bridge = CvBridge()
        self.camera_image = None
        self.yolo_image = None
        self.voice_text = ""
        self.voice_command = ""
        self.detected_objects = ""
        self.linear_imu = None
        self.angular_imu = None
        self.lidar_points = []
        self.battery_percentage = None
        self.temperature = None
        self.cpu_usage = None

        # Publishers and Subscriptions
        self.voice_text_pub = self.create_publisher(String, '/voice_text', 10)
        self.create_subscription(Image, '/oakd/rgb/preview/image_raw', self.cam_cb, 10)
        self.create_subscription(Image, '/yolo_image_raw', self.yolo_cb, 10)
        self.create_subscription(String, '/voice_text', self.voice_text_cb, 10)
        self.create_subscription(String, '/voice_command', self.voice_cmd_cb, 10)
        self.create_subscription(String, '/detected_objects', self.detected_objects_cb, 10)
        self.create_subscription(Imu, '/rpi_13/imu', self.imu_cb, 10)
        self.create_subscription(LaserScan, '/scan', self.lidar_cb, 10)
        self.create_subscription(BatteryState, '/rpi_13/battery_state', self.battery_cb, 10)
        self.create_subscription(DiagnosticArray, '/diagnostics', self.diagnostics_cb, 10)
        self.is_docked = None
        self.create_subscription(DockStatus, '/rpi_13/dock_status', self.dock_status_cb, 10)

    def cam_cb(self, msg):
        self.camera_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def yolo_cb(self, msg):
        self.yolo_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def voice_text_cb(self, msg):
        self.voice_text = msg.data

    def voice_cmd_cb(self, msg):
        self.voice_command = msg.data

    def detected_objects_cb(self, msg):
        self.detected_objects = msg.data

    def imu_cb(self, msg):
        self.linear_imu = (msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z)
        self.angular_imu = (msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z)

    def lidar_cb(self, msg):
        self.lidar_points = [(r * np.cos(a) * 70, r * np.sin(a) * 70)
                     for r, a in zip(msg.ranges, np.arange(msg.angle_min, msg.angle_max, msg.angle_increment)) if np.isfinite(r)]
        #self.lidar_points = [(r * np.cos(a) * 25, r * np.sin(a) * 25)
                             #for r, a in zip(msg.ranges, np.arange(msg.angle_min, msg.angle_max, msg.angle_increment)) if np.isfinite(r)]

    def battery_cb(self, msg):
        self.battery_percentage = msg.percentage
        self.temperature = msg.temperature

    def diagnostics_cb(self, msg):
        # Extract CPU usage from diagnostics (assuming a standard key-value pair)
        for status in msg.status:
            for kv in status.values:
                if kv.key.lower() == 'cpu usage':
                    try:
                        self.cpu_usage = float(kv.value.strip('%')) / 100.0
                    except ValueError:
                        self.cpu_usage = None
    def dock_status_cb(self, msg):
        self.is_docked = msg.is_docked

def main(args=None):
    rclpy.init(args=args)
    node = TurtlebotNode()
    app = QApplication(sys.argv)
    gui = TurtlebotGUI(node)
    gui.show()
    try:
        sys.exit(app.exec_())
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()