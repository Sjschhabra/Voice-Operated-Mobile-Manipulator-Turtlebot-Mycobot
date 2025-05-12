# File: bringup_launch.py

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='voice_controlled_turtlebot',
            executable='mic_listener_node',
            name='mic_listener_node',
            output='screen'
        ),
        #Node(
            #package='voice_controlled_turtlebot',
            #executable='voice_controlled_turtlebot_supernode',
            #name='voice_controlled_turtlebot_supernode',
            #output='screen'
        #),
        Node(
            package='voice_controlled_turtlebot',
            executable='command_parser_node',
            name='command_parser_node',
            output='screen'
        ),
        Node(
            package='voice_controlled_turtlebot',
            executable='movement_controller_node',
            name='movement_controller_node',
            output='screen'
        ),
        Node(
            package='voice_controlled_turtlebot',
            executable='object_detector_node',
            name='object_detector_node',
            output='screen'
        ),
        Node(
            package='voice_controlled_turtlebot',
            executable='web_dashboard_node',
            name='web_dashboard_node',
            output='screen'
        ),
    ])

