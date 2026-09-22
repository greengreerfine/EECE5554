import csv
from pathlib import Path

from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


LAB_DIR = Path.home() / "EECE5554" / "Lab1"
DATA_DIR = LAB_DIR / "data"
OUTPUT_DIR = LAB_DIR / "analysis"


def extract_bag(name):
    bag_path = DATA_DIR / name
    output_path = OUTPUT_DIR / f"{name}.csv"

    reader = SequentialReader()

    storage_options = StorageOptions(
        uri=str(bag_path),
        storage_id="mcap"
    )

    converter_options = ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr"
    )

    reader.open(storage_options, converter_options)

    topic_types = {
        topic.name: topic.type
        for topic in reader.get_all_topics_and_types()
    }

    gps_type = get_message(topic_types["/gps"])

    rows = []

    while reader.has_next():
        topic, data, bag_timestamp = reader.read_next()

        if topic != "/gps":
            continue

        msg = deserialize_message(data, gps_type)

        ros_time = (
            msg.header.stamp.sec
            + msg.header.stamp.nanosec / 1e9
        )

        rows.append([
            ros_time,
            msg.latitude,
            msg.longitude,
            msg.altitude,
            msg.utm_easting,
            msg.utm_northing,
            msg.zone,
            msg.letter,
            msg.hdop
        ])

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "time",
            "latitude",
            "longitude",
            "altitude",
            "utm_easting",
            "utm_northing",
            "zone",
            "letter",
            "hdop"
        ])

        writer.writerows(rows)

    print(f"{name}: {len(rows)} messages -> {output_path}")


for bag_name in [
    "open_stationary",
    "occluded_stationary",
    "walking"
]:
    extract_bag(bag_name)
