from setuptools import find_packages, setup

package_name = 'voice_controlled_turtlebot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/voice_controlled_turtlebot/launch', ['launch/voice_controlled_turtlebot.launch.py']), 
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='anushkasatav',
    maintainer_email='anoushkasatav002@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mic_listener_node = voice_controlled_turtlebot.mic_listener_node:main',
            'voice_controlled_turtlebot_supernode = voice_controlled_turtlebot.voice_controlled_turtlebot_supernode:main',
            'command_parser_node = voice_controlled_turtlebot.command_parser_node:main',
            'movement_controller_node = voice_controlled_turtlebot.movement_controller_node:main',
            'object_detector_node = voice_controlled_turtlebot.object_detector_node:main',
            'web_dashboard_node = voice_controlled_turtlebot.web_dashboard_node:main',
        ],
    },
)
