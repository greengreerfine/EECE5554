from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    port = LaunchConfiguration('port')

    return LaunchDescription([
        DeclareLaunchArgument(
            'port',
            default_value='/dev/ttyUSB0',
            description='Serial port for the GNSS receiver'
        ),

        Node(
            package='gps_driver',
            executable='standalone_driver',
            name='gps_driver',
            parameters=[{'port': port}],
            output='screen'
        )
    ])