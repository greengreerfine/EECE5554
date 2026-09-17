import serial
import utm

from datetime import datetime, timezone

import rclpy
from rclpy.node import Node

from gps_msgs.msg import Customgps


class GPSDriver(Node):

    def __init__(self):
        super().__init__('gps_driver')

        # Serial port is supplied as a ROS 2 parameter.
        self.declare_parameter('port', '/dev/ttyUSB0')
        port = self.get_parameter('port').value

        # GPS receiver communicates at 4800 baud.
        self.serial_port = serial.Serial(
            port=port,
            baudrate=4800,
            timeout=1.0
        )

        # Publish Customgps messages on /gps.
        self.publisher_ = self.create_publisher(
            Customgps,
            '/gps',
            10
        )

        # Check the serial port repeatedly.
        self.timer = self.create_timer(0.1, self.read_gps)

        self.get_logger().info(f'GPS driver started on {port}')


    def convert_to_decimal_degrees(self, value, direction):
        """
        Convert NMEA DDMM.MMMM / DDDMM.MMMM
        into signed decimal degrees.
        """

        value = float(value)

        degrees = int(value // 100)
        minutes = value - degrees * 100

        decimal_degrees = degrees + minutes / 60.0

        if direction in ('S', 'W'):
            decimal_degrees = -decimal_degrees

        return decimal_degrees


    def gps_time_to_epoch(self, utc_string):
        """
        Convert GPGGA UTC time HHMMSS.SS
        to Unix epoch seconds + nanoseconds.
        """

        hour = int(utc_string[0:2])
        minute = int(utc_string[2:4])

        seconds_part = utc_string[4:]

        if '.' in seconds_part:
            second_string, fraction_string = seconds_part.split('.', 1)
        else:
            second_string = seconds_part
            fraction_string = ''

        second = int(second_string)

        # Convert fractional second to nanoseconds.
        nanosec = int((fraction_string + '000000000')[:9])

        # Use system clock only for today's date.
        today = datetime.now().date()

        gps_datetime = datetime(
            today.year,
            today.month,
            today.day,
            hour,
            minute,
            second,
            tzinfo=timezone.utc
        )

        epoch_sec = int(gps_datetime.timestamp())

        return epoch_sec, nanosec


    def read_gps(self):

        try:
            raw_line = self.serial_port.readline()

            if not raw_line:
                return

            sentence = raw_line.decode(
                'ascii',
                errors='ignore'
            ).rstrip('\r\n')

            # Ignore everything except GPGGA.
            if not sentence.startswith('$GPGGA'):
                return

            fields = sentence.split(',')

            utc = fields[1]

            latitude_raw = fields[2]
            latitude_direction = fields[3]

            longitude_raw = fields[4]
            longitude_direction = fields[5]

            hdop = float(fields[8])
            altitude = float(fields[9])

            # Convert latitude and longitude.
            latitude = self.convert_to_decimal_degrees(
                latitude_raw,
                latitude_direction
            )

            longitude = self.convert_to_decimal_degrees(
                longitude_raw,
                longitude_direction
            )

            # Convert latitude/longitude to UTM.
            easting, northing, zone_number, zone_letter = \
                utm.from_latlon(latitude, longitude)

            # Convert GPS UTC into ROS timestamp.
            epoch_sec, nanosec = self.gps_time_to_epoch(utc)

            # Create ROS 2 message.
            msg = Customgps()

            msg.header.frame_id = 'GPS1_Frame'
            msg.header.stamp.sec = epoch_sec
            msg.header.stamp.nanosec = nanosec

            msg.latitude = latitude
            msg.longitude = longitude
            msg.altitude = altitude

            msg.utm_easting = easting
            msg.utm_northing = northing

            msg.zone = zone_number
            msg.letter = zone_letter

            msg.hdop = hdop
            msg.gpgga_read = sentence

            # Publish to /gps.
            self.publisher_.publish(msg)

            self.get_logger().info(
                f'Published GPS: {latitude}, {longitude}'
            )

        except (ValueError, IndexError) as error:
            self.get_logger().warning(
                f'Could not parse GPGGA sentence: {error}'
            )


def main(args=None):

    rclpy.init(args=args)

    node = GPSDriver()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.serial_port.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()