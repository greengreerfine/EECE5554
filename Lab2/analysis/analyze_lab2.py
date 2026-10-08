#!/usr/bin/env python3
"""EECE5554 Lab2: stationary GNSS precision and walking-line analysis from GGA NMEA.

Reads five pre-split .nmea files. Does not modify source data.
Outputs metrics CSV and per-epoch CSV under analysis/results/.
"""
from pathlib import Path
from collections import Counter
import csv
import math
import numpy as np
from pyproj import Transformer

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data'
OUT = BASE / 'analysis' / 'results'
OUT.mkdir(parents=True, exist_ok=True)

STATIONARY = ['open_standalone', 'open_rtk', 'occluded_standalone', 'occluded_rtk']
ALL = STATIONARY + ['walking_rtk']
transformer = Transformer.from_crs('EPSG:4326', 'EPSG:32610', always_xy=True)


def coord(value, hemi):
    number = float(value)
    deg = int(number // 100)
    result = deg + (number - 100 * deg) / 60.0
    return -result if hemi in ('W', 'S') else result


def as_float(value):
    try:
        return float(value) if value.strip() else float('nan')
    except ValueError:
        return float('nan')


def as_int(value):
    try:
        return int(value) if value.strip() else 0
    except ValueError:
        return 0


def parse_file(name):
    path = DATA / f'{name}.nmea'
    if not path.is_file():
        raise FileNotFoundError(path)
    rows = []
    with path.open(encoding='utf-8', errors='replace') as f:
        for line_no, line in enumerate(f, 1):
            parts = line.strip().split(',')
            if parts[0] not in ('$GPGGA', '$GNGGA'):
                continue
            if len(parts) < 10:
                print(f'WARNING {name}:{line_no}: short GGA skipped')
                continue
            t = parts[1]
            quality = as_int(parts[6])
            sat = as_float(parts[7]); hdop = as_float(parts[8]); altitude = as_float(parts[9])
            latitude = longitude = easting = northing = float('nan')
            if quality > 0 and all(parts[i].strip() for i in (2, 3, 4, 5)):
                try:
                    latitude = coord(parts[2], parts[3]); longitude = coord(parts[4], parts[5])
                    easting, northing = transformer.transform(longitude, latitude)
                except (ValueError, OverflowError):
                    print(f'WARNING {name}:{line_no}: invalid coordinates')
            rows.append(dict(dataset=name, time_utc=t, fix_quality=quality,
                             satellites=sat, hdop=hdop, altitude_m=altitude,
                             latitude=latitude, longitude=longitude,
                             easting_m=easting, northing_m=northing))
    if not rows:
        raise ValueError(f'{path}: no GGA records')
    return rows


def finite_mean(values):
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    return float(np.mean(vals)) if len(vals) else float('nan')


def stationary_metrics(rows, label):
    valid = [r for r in rows if np.isfinite(r['easting_m']) and np.isfinite(r['northing_m'])]
    if len(valid) < 2:
        raise ValueError(f'{label}: fewer than 2 valid horizontal positions')
    E = np.array([r['easting_m'] for r in valid]); N = np.array([r['northing_m'] for r in valid]);
    H = np.array([r['altitude_m'] for r in valid]); H = H[np.isfinite(H)]
    center_e, center_n = float(np.mean(E)), float(np.mean(N))
    distances = np.hypot(E-center_e, N-center_n)
    std_e, std_n = float(np.std(E, ddof=0)), float(np.std(N, ddof=0))
    counts = Counter(r['fix_quality'] for r in rows)
    result = {
        'dataset':label, 'epochs':len(rows), 'valid_position_epochs':len(valid),
        'centroid_easting_m':center_e, 'centroid_northing_m':center_n,
        'median_deviation_m':float(np.median(distances)),
        'p95_deviation_m':float(np.percentile(distances, 95)),
        'std_easting_m':std_e, 'std_northing_m':std_n,
        '2drms_m':2.0*math.hypot(std_e, std_n),
        'std_altitude_m':float(np.std(H, ddof=0)) if len(H)>=2 else float('nan'),
        'mean_satellites':finite_mean([r['satellites'] for r in valid]),
        'mean_hdop':finite_mean([r['hdop'] for r in valid]),
    }
    for quality in (0, 1, 2, 4, 5):
        result[f'quality_{quality}_pct'] = 100.0 * counts[quality] / len(rows)
    return result


def walking_metrics(rows):
    valid = [r for r in rows if np.isfinite(r['easting_m']) and np.isfinite(r['northing_m'])]
    if len(valid)<2:
        raise ValueError('walking_rtk: fewer than 2 valid positions')
    points = np.array([[r['easting_m'],r['northing_m']] for r in valid], dtype=float)
    mean = points.mean(axis=0)
    centered = points - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    direction = vt[0]
    perpendicular = centered @ vt[1]
    delta = points[-1] - points[0]
    return {
        'epochs':len(rows), 'valid_position_epochs':len(valid),
        'start_end_displacement_m':float(np.linalg.norm(delta)),
        'cumulative_gnss_path_m':float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),
        'perpendicular_rmse_m':float(np.sqrt(np.mean(perpendicular**2))),
        'max_abs_perpendicular_m':float(np.max(np.abs(perpendicular))),
        'quality_distribution':str(dict(sorted(Counter(r['fix_quality'] for r in rows).items()))),
    }


def write_csv(path, rows):
    if not rows: return
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    print('Saved:', path)


def main():
    all_rows = {name:parse_file(name) for name in ALL}
    metrics = [stationary_metrics(all_rows[name],name) for name in STATIONARY]
    fixed = [r for r in all_rows['open_rtk'] if r['fix_quality']==4]
    if fixed:
        metrics.insert(2, stationary_metrics(fixed, 'open_rtk_fixed_only'))
    else:
        print('WARNING: open_rtk has no fixed epochs')
    write_csv(OUT/'stationary_metrics.csv',metrics)
    write_csv(OUT/'epochs.csv',[r for name in ALL for r in all_rows[name]])
    walking = walking_metrics(all_rows['walking_rtk'])
    write_csv(OUT/'walking_metrics.csv',[walking])
    print('\nStationary summary (precision, NOT surveyed accuracy):')
    for m in metrics:
        print(f"{m['dataset']:25} n={m['valid_position_epochs']:4d}/{m['epochs']:4d} "
              f"median={m['median_deviation_m']:.3f} m 2DRMS={m['2drms_m']:.3f} m")
    print('\nWalking summary:')
    for k,v in walking.items(): print(f'  {k}: {v}')
    print('\nImportant: all-epochs position precision uses valid coordinates only; fix-quality percentages use all GGA epochs.')


if __name__ == '__main__':
    main()
