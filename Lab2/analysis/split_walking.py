from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

BASE = Path.home() / "EECE5554/Lab2"

SOURCE = BASE / "data/walking.nmea"
OUTPUT = BASE / "data/walking_rtk.nmea"

START = 3627.00  # 00:36:27
END = 3947.00    # 00:39:47


def nmea_to_decimal(value, direction):
    raw = float(value)
    degrees = int(raw // 100)
    minutes = raw - degrees * 100

    result = degrees + minutes / 60

    if direction in ("S", "W"):
        result = -result

    return result


def haversine(lat1, lon1, lat2, lon2):
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


selected = []
positions = []

with SOURCE.open() as f:
    for line in f:
        fields = line.strip().split(",")

        if fields[0] not in ("$GPGGA", "$GNGGA"):
            continue

        if not fields[1]:
            continue

        timestamp = float(fields[1])

        if START <= timestamp <= END:
            selected.append(line)

            if fields[2] and fields[4] and int(fields[6] or 0) > 0:
                lat = nmea_to_decimal(fields[2], fields[3])
                lon = nmea_to_decimal(fields[4], fields[5])

                positions.append((lat, lon))


if len(positions) < 2:
    raise SystemExit("Insufficient valid positions; output not written.")


start = positions[0]
end = positions[-1]

displacement = haversine(
    start[0], start[1],
    end[0], end[1]
)

cumulative = 0.0

for a, b in zip(positions, positions[1:]):
    cumulative += haversine(
        a[0], a[1],
        b[0], b[1]
    )


print("Walking segment inspection")
print("--------------------------")
print("Start:", START)
print("End:", END)
print("GGA epochs:", len(selected))
print("Valid positions:", len(positions))
print("Start-end displacement:", round(displacement, 2), "m")
print("Cumulative GNSS path:", round(cumulative, 2), "m")

if 200 <= displacement <= 300:
    print("Displacement requirement: PASS")
else:
    print("Displacement requirement: REVIEW")

print("Note: displacement alone does not establish straightness.")

OUTPUT.write_text("".join(selected))

print("Saved:", OUTPUT)
