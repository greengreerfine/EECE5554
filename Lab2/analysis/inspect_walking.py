from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

FILE = Path.home() / "EECE5554/Lab2/data/walking.nmea"


def nmea_to_decimal(value, direction):
    if not value:
        return None

    raw = float(value)
    degrees = int(raw // 100)
    minutes = raw - degrees * 100

    decimal = degrees + minutes / 60

    if direction in ("S", "W"):
        decimal = -decimal

    return decimal


def distance(lat1, lon1, lat2, lon2):
    R = 6371000

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


records = []

with open(FILE) as f:
    for line in f:
        fields = line.strip().split(",")

        if fields[0] not in ("$GPGGA", "$GNGGA"):
            continue

        quality = int(fields[6] or 0)

        if not fields[2] or not fields[4]:
            continue

        lat = nmea_to_decimal(fields[2], fields[3])
        lon = nmea_to_decimal(fields[4], fields[5])

        records.append((fields[1], quality, lat, lon))


if not records:
    raise SystemExit("No valid positions found")


start = records[0]
previous = start

cumulative = 0

print(
    f"{'Time':<12}"
    f"{'Fix':<6}"
    f"{'From Start (m)':<18}"
    f"{'Cumulative (m)':<18}"
)

for i, record in enumerate(records):

    time, quality, lat, lon = record

    if i > 0:
        cumulative += distance(
            previous[2],
            previous[3],
            lat,
            lon
        )

    from_start = distance(
        start[2],
        start[3],
        lat,
        lon
    )

    if i % 20 == 0 or i == len(records) - 1:
        print(
            f"{time:<12}"
            f"{quality:<6}"
            f"{from_start:<18.2f}"
            f"{cumulative:<18.2f}"
        )

    previous = record

print()
print("Valid position epochs:", len(records))
print("Total cumulative distance:", round(cumulative, 2), "m")
