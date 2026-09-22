import csv
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


BASE = Path.home() / "EECE5554" / "Lab1" / "analysis"


def load_csv(filename):
    data = {
        "time": [],
        "latitude": [],
        "longitude": [],
        "altitude": [],
        "utm_easting": [],
        "utm_northing": [],
        "hdop": [],
    }

    with open(BASE / filename, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            for key in data:
                data[key].append(float(row[key]))

    for key in data:
        data[key] = np.array(data[key])

    # Convert absolute timestamps to elapsed seconds.
    data["elapsed_time"] = data["time"] - data["time"][0]

    return data


open_data = load_csv("open_stationary.csv")
occ_data = load_csv("occluded_stationary.csv")
walking = load_csv("walking.csv")


# ---------------------------------------------------------
# Basic statistics
# ---------------------------------------------------------

def print_stats(name, data):
    print(f"\n{name}")
    print("-" * len(name))

    print(
        f"Easting mean/std : "
        f"{np.mean(data['utm_easting']):.3f} / "
        f"{np.std(data['utm_easting']):.3f} m"
    )

    print(
        f"Northing mean/std: "
        f"{np.mean(data['utm_northing']):.3f} / "
        f"{np.std(data['utm_northing']):.3f} m"
    )

    print(
        f"Altitude mean/std: "
        f"{np.mean(data['altitude']):.3f} / "
        f"{np.std(data['altitude']):.3f} m"
    )

    print(
        f"HDOP mean        : "
        f"{np.mean(data['hdop']):.3f}"
    )


print_stats("OPEN STATIONARY", open_data)
print_stats("OCCLUDED STATIONARY", occ_data)


# ---------------------------------------------------------
# 1. Stationary Northing vs Easting scatter plot
# ---------------------------------------------------------

plt.figure(figsize=(8, 7))

plt.scatter(
    open_data["utm_easting"],
    open_data["utm_northing"],
    s=14,
    alpha=0.65,
    label="Open"
)

plt.scatter(
    occ_data["utm_easting"],
    occ_data["utm_northing"],
    s=14,
    alpha=0.65,
    label="Occluded"
)

plt.xlabel("UTM Easting (m)")
plt.ylabel("UTM Northing (m)")
plt.title("Stationary GPS: Northing vs Easting")
plt.legend()
plt.grid(True)
plt.axis("equal")
plt.tight_layout()

plt.savefig(
    BASE / "stationary_scatter.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 2. Stationary altitude plot
# ---------------------------------------------------------

plt.figure(figsize=(9, 5))

plt.plot(
    open_data["elapsed_time"],
    open_data["altitude"],
    label="Open"
)

plt.plot(
    occ_data["elapsed_time"],
    occ_data["altitude"],
    label="Occluded"
)

plt.xlabel("Elapsed Time (s)")
plt.ylabel("Altitude (m)")
plt.title("Stationary GPS Altitude")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    BASE / "stationary_altitude.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 3. Stationary histograms
#
# We use position offsets from each dataset's own mean.
# This makes the spread / noise easier to compare.
# ---------------------------------------------------------

open_e_offset = (
    open_data["utm_easting"]
    - np.mean(open_data["utm_easting"])
)

occ_e_offset = (
    occ_data["utm_easting"]
    - np.mean(occ_data["utm_easting"])
)

open_n_offset = (
    open_data["utm_northing"]
    - np.mean(open_data["utm_northing"])
)

occ_n_offset = (
    occ_data["utm_northing"]
    - np.mean(occ_data["utm_northing"])
)


fig, axes = plt.subplots(2, 1, figsize=(9, 8))

axes[0].hist(
    open_e_offset,
    bins=30,
    alpha=0.55,
    label="Open"
)

axes[0].hist(
    occ_e_offset,
    bins=30,
    alpha=0.55,
    label="Occluded"
)

axes[0].set_xlabel("Easting Offset from Mean (m)")
axes[0].set_ylabel("Count")
axes[0].set_title("Stationary Easting Distribution")
axes[0].legend()
axes[0].grid(True)


axes[1].hist(
    open_n_offset,
    bins=30,
    alpha=0.55,
    label="Open"
)

axes[1].hist(
    occ_n_offset,
    bins=30,
    alpha=0.55,
    label="Occluded"
)

axes[1].set_xlabel("Northing Offset from Mean (m)")
axes[1].set_ylabel("Count")
axes[1].set_title("Stationary Northing Distribution")
axes[1].legend()
axes[1].grid(True)

plt.tight_layout()

plt.savefig(
    BASE / "stationary_histogram.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 4. Walking / moving Northing vs Easting scatter plot
# ---------------------------------------------------------

plt.figure(figsize=(8, 7))

plt.scatter(
    walking["utm_easting"],
    walking["utm_northing"],
    s=12
)

# Mark the recorded start and end positions.
plt.scatter(
    walking["utm_easting"][0],
    walking["utm_northing"][0],
    s=70,
    label="Start"
)

plt.scatter(
    walking["utm_easting"][-1],
    walking["utm_northing"][-1],
    s=70,
    label="End"
)

plt.xlabel("UTM Easting (m)")
plt.ylabel("UTM Northing (m)")
plt.title("Walking GPS Trajectory")
plt.legend()
plt.grid(True)
plt.axis("equal")
plt.tight_layout()

plt.savefig(
    BASE / "walking_scatter.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 5. Walking altitude plot
# ---------------------------------------------------------

plt.figure(figsize=(9, 5))

plt.plot(
    walking["elapsed_time"],
    walking["altitude"]
)

plt.xlabel("Elapsed Time (s)")
plt.ylabel("Altitude (m)")
plt.title("Walking GPS Altitude")
plt.grid(True)
plt.tight_layout()

plt.savefig(
    BASE / "walking_altitude.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# Walking distance statistics
# ---------------------------------------------------------

delta_e = np.diff(walking["utm_easting"])
delta_n = np.diff(walking["utm_northing"])

segment_distances = np.sqrt(
    delta_e**2 + delta_n**2
)

path_length = np.sum(segment_distances)

straight_line_distance = math.sqrt(
    (
        walking["utm_easting"][-1]
        - walking["utm_easting"][0]
    ) ** 2
    +
    (
        walking["utm_northing"][-1]
        - walking["utm_northing"][0]
    ) ** 2
)

print("\nWALKING")
print("-------")

print(
    f"Recorded path length      : "
    f"{path_length:.2f} m"
)

print(
    f"Start-to-end displacement : "
    f"{straight_line_distance:.2f} m"
)

print("\nSaved plots:")

for filename in [
    "stationary_scatter.png",
    "stationary_altitude.png",
    "stationary_histogram.png",
    "walking_scatter.png",
    "walking_altitude.png",
]:
    print(BASE / filename)
