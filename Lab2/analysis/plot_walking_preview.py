from pathlib import Path
import matplotlib.pyplot as plt
from pyproj import Transformer

BASE = Path.home() / "EECE5554/Lab2"
INPUT = BASE / "data/walking.nmea"

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32610",
    always_xy=True
)

times = []
eastings = []
northings = []
qualities = []


def nmea_to_decimal(value, hemisphere):
    raw = float(value)
    degrees = int(raw // 100)
    minutes = raw - degrees * 100

    result = degrees + minutes / 60

    if hemisphere in ("S", "W"):
        result = -result

    return result


with INPUT.open() as f:
    for line in f:
        fields = line.strip().split(",")

        if fields[0] not in ("$GPGGA", "$GNGGA"):
            continue

        if not fields[2] or not fields[4]:
            continue

        quality = int(fields[6] or 0)

        if quality == 0:
            continue

        lat = nmea_to_decimal(fields[2], fields[3])
        lon = nmea_to_decimal(fields[4], fields[5])

        e, n = transformer.transform(lon, lat)

        times.append(fields[1])
        eastings.append(e)
        northings.append(n)
        qualities.append(quality)


e0 = eastings[0]
n0 = northings[0]

x = [e - e0 for e in eastings]
y = [n - n0 for n in northings]

fig, ax = plt.subplots(figsize=(10, 8))

scatter = ax.scatter(
    x,
    y,
    c=qualities,
    cmap="viridis",
    s=12
)

ax.scatter(
    x[0], y[0],
    marker="o",
    s=120,
    label="Start"
)

ax.scatter(
    x[-1], y[-1],
    marker="X",
    s=120,
    label="End"
)

for i in range(0, len(x), 30):
    ax.annotate(
        times[i][:6],
        (x[i], y[i]),
        fontsize=7
    )

ax.set_xlabel("Relative Easting (m)")
ax.set_ylabel("Relative Northing (m)")
ax.set_title("Walking RTK — Full Trajectory Preview")

ax.set_aspect("equal", adjustable="box")
ax.grid(True)
ax.legend()

plt.colorbar(scatter, label="Fix Quality")

OUTPUT = BASE / "analysis/walking_preview.png"

plt.savefig(OUTPUT, dpi=200, bbox_inches="tight")

print("Saved:", OUTPUT)

plt.show()
