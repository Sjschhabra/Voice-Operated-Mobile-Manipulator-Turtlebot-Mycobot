# 🐢 Intelligent Voice Operated Mobile Manipulator  
**Real-Time Object Detection & Navigation using TurtleBot4 and MyCobot**

![Project Banner](https://ras598-2025-s-team11.github.io/assets/logo.png) <!-- Replace with actual image path -->

## 🚀 Overview
This project presents a multi-modal robotic system integrating **voice interaction**, **object detection**, and **robotic manipulation**. Using **ROS 2**, a **TurtleBot4** base, and a **MyCobot arm**, we developed a voice-guided mobile robot capable of recognizing objects, executing navigation commands, and performing precise arm motions.

Designed for the **RAS 598: Experimentation and Deployment of Robotic Systems** course at Arizona State University, this robot emphasizes real-time human-robot interaction and awareness-driven autonomy.

---

## 🔍 Research Question
> _How can a mobile robot effectively combine vision, speech, navigation, and manipulation to create a responsive and intelligent system for real-world environments?_

---

## 🧠 Key Features
- 🎤 **Voice Interaction**: Local speech-to-text using Whisper.cpp  
- 🔍 **Object Detection**: Real-time classification with YOLOv8 (Nano)  
- 🖥 **GUI Dashboard**: PyQt5-based interface visualizing sensory and perception data  
- 🤖 **Robotic Arm Control**: MyCobot arm with custom IK routines  
- 📡 **Sensor Fusion**: Combines LiDAR, IMU, and RGB data for perception  
- 🧩 **Modular ROS 2 Nodes**: Designed for scalability and reliability  

---

## 🎯 Project Timeline

| Week | Milestone |
|------|-----------|
| 7    | Hardware finalized, initial architecture design |
| 8    | ROS 2 setup and TurtleBot4 base integration |
| 9    | YOLOv8 Nano for object detection deployed |
| 10   | Voice command system integrated (Whisper.cpp) |
| 11   | GUI dashboard built using PyQt5 |
| 12   | ROS 2 node integration complete |
| 13   | Field testing with TurtleBot4 |
| 14   | Debugging, error handling, fallback mechanisms |
| 15   | Final documentation, demo, and polish |
| 16   | Project presented at ASU Innovation Showcase |

---

## 📦 System Architecture

### Core ROS 2 Nodes
- `mic_listener_node`: Converts voice to text using Whisper.cpp
- `command_parser_node`: Interprets text into robot commands
- `object_detector_node`: YOLOv8-based real-time object recognition
- `movement_controller_node`: Handles navigation and velocity commands
- `web_dashboard_node`: PyQt5 dashboard for real-time monitoring

### Subscribed Topics
- `/oakd/rgb/preview/image_raw` – RGB camera stream  
- `/voice_text`, `/voice_command` – Transcribed and parsed commands  
- `/scan` – LiDAR data  
- `/rpi_13/imu` – IMU data  
- `/detected_objects` – Object labels from YOLO  

### Published Topics
- `/cmd_vel` – Navigation control  
- `/arm_pose` – Target pose for MyCobot  
- `/voice_text` – GUI command feedback  

---

## 🖼 GUI (PyQt5)

- **Live Video**: Raw and YOLO-annotated feeds  
- **Real-Time Plots**: LiDAR, IMU, detected object labels  
- **Command Feedback**: Color-coded logs, emojis, and voice confirmations  
- **Dashboard Tabs**: Organized into camera, speech, sensor, and logs  

---

## 🗣️ Voice Commands Supported

| Command Group | Examples |
|---------------|----------|
| **Navigation** | `move_forward`, `turn_left`, `stop`, `dock` |
| **Perception** | `look_for_object`, `go_to_object`, `take_a_picture` |
| **Arm Control** | `grasp`, `wave_emote`, `home_position` |
| **Miscellaneous** | `scan`, `return_to_base`, `repeat` |

---

## 🔧 Design Considerations

- **Audio**: Whisper.cpp used for local inference; stable on Pi-class CPUs  
- **Detection**: YOLOv8 Nano selected for balance of speed and accuracy  
- **Communication**: Cyclone DDS over Ethernet for ROS 2 reliability  
- **Fallbacks**: GUI interaction to recover from mic or hardware failures  

---

## 🌍 Future Work

- Integrate full **voice-to-arm manipulation** workflows  
- Add **task-based planning** (e.g. fetch red ball)  
- GUI updates: battery indicator, network diagnostics  
- More robust **scene understanding** and autonomous cycles  

---

## 🎓 Academic Context

Developed as part of **RAS 598: Experimentation and Deployment of Robotic Systems**  
**Instructor**: Prof. Dan Aukes  
**Institution**: Arizona State University  
**Semester**: Spring 2025  

---

## 👥 Team Members

- Sameerjeet Singh Chhabra  
- Anushka Gangadhar Satav  
- Adithya Konda  

---

## 📹 Demo Videos & Links

- 🌐 [Project Website](https://ras598-2025-s-team11.github.io/)
- ▶️ **[Final Demo Video](#)** *(link to be added)*  
- ▶️ **[Innovation Showcase Presentation](#)** *(link to be added)*

---

## 🛠️ Setup Instructions

Coming soon! Will include:
- `requirements.txt`
- ROS 2 node launch instructions
- Hardware setup notes

---

## 📄 License

This project is for academic use under Arizona State University's course policy. Contact the team for reuse or collaboration inquiries.


