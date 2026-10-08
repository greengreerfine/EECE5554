#!/usr/bin/env python3
"""Reconstruct ROS 2 MCAP bags from field-collected NMEA; NOT original field recordings.
Usage (after sourcing ROS 2 and workspace): python3 analysis/nmea_to_rosbag.py
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import utm
import rosbag2_py
from gps_msgs.msg import Customrtk
from rclpy.serialization import serialize_message

BASE = Path(__file__).resolve().parents[1]
# NMEA GGA contains UTC time but NO DATE. Dates below come from the field log.
# Walking collected Oct 1 at ~6pm Seattle = Oct 2 UTC.
DATES_UTC = {
    'open_standalone': '2026-10-06',
    'open_rtk': '2026-10-06',
    'occluded_standalone': '2026-10-06',
    'occluded_rtk': '2026-10-06',
    'walking_rtk': '2026-10-02',
}


def number(s, default=0.0):
    return float(s) if s.strip() else default


def integer(s, default=0):
    return int(s) if s.strip() else default


def decimal(value, direction):
    value = float(value)
    deg = int(value // 100)
    result = deg + (value - deg * 100) / 60
    return -result if direction in ('S', 'W') else result


def timestamp_ns(date, utc):
    hour, minute = int(utc[:2]), int(utc[2:4])
    sec_text = utc[4:]
    sec_str, _, fraction = sec_text.partition('.')
    sec = int(sec_str)
    nanos = int((fraction + '000000000')[:9])
    dt = datetime.fromisoformat(date).replace(hour=hour, minute=minute, second=sec,
                                             tzinfo=timezone.utc)
    return int(dt.timestamp()) * 1_000_000_000 + nanos


def make_message(line, date):
    parts = line.strip().split(',')
    if len(parts) < 14 or parts[0] not in ('$GPGGA', '$GNGGA'):
        return None
    # Match the tested driver: no-fix with blank lat/lon cannot publish a Customrtk.
    if not all(parts[i].strip() for i in (1, 2, 3, 4, 5)):
        return None
    lat = decimal(parts[2], parts[3])
    lon = decimal(parts[4], parts[5])
    e, n, zone, letter = utm.from_latlon(lat, lon)
    stamp = timestamp_ns(date, parts[1])
    msg = Customrtk()
    msg.header.frame_id = 'GPS1_Frame'
    msg.header.stamp.sec = stamp // 1_000_000_000
    msg.header.stamp.nanosec = stamp % 1_000_000_000
    msg.latitude, msg.longitude, msg.altitude = lat, lon, number(parts[9])
    msg.utm_easting, msg.utm_northing = e, n
    msg.zone, msg.letter = zone, letter
    msg.hdop = number(parts[8])
    msg.gpgga_read = line.strip()
    msg.fix_quality = integer(parts[6])
    msg.num_satellites = integer(parts[7])
    msg.correction_age = number(parts[13])
    return msg, stamp


def convert(name, date):
    source = BASE / 'data' / f'{name}.nmea'
    destination = BASE / 'data' / name
    if not source.is_file():
        raise FileNotFoundError(source)
    if destination.exists():
        print(f'SKIP {name}: {destination} already exists (never overwrite)')
        return
    writer = rosbag2_py.SequentialWriter()
    writer.open(rosbag2_py.StorageOptions(uri=str(destination), storage_id='mcap'),
                rosbag2_py.ConverterOptions('cdr', 'cdr'))
    writer.create_topic(rosbag2_py.TopicMetadata(
    id=0,
    name='/gps',
    type='gps_msgs/msg/Customrtk',
    serialization_format='cdr'))
    total = written = 0
    qualities = Counter()
    previous = None
    with source.open(encoding='ascii', errors='replace') as f:
        for line in f:
            if not line.startswith(('$GPGGA', '$GNGGA')):
                continue
            total += 1
            try:
                result = make_message(line, date)
            except (ValueError, IndexError, OverflowError) as exc:
                print(f'WARN {name}: skipped malformed epoch: {exc}')
                continue
            if result is None:
                continue
            msg, stamp = result
            if previous is not None and stamp < previous:
                raise RuntimeError(f'{name}: UTC timestamps reversed; verify date and midnight rollover')
            previous = stamp
            writer.write('/gps', serialize_message(msg), stamp)
            written += 1
            qualities[msg.fix_quality] += 1
    del writer  # finalize metadata.yaml
    print(f'{name}: {written}/{total} published messages; quality={dict(sorted(qualities.items()))}')
    print(f'  Saved: {destination}')


def main():
    for name, date in DATES_UTC.items():
        convert(name, date)
    print('\nReconstructed bags: NOT originally recorded on site. State this in README.')


if __name__ == '__main__':
    main()
