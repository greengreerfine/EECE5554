#!/usr/bin/env python3
"""Generate six EECE5554 Lab2 rubric plots from analysis/results/epochs.csv.
Run: python3 analysis/plot_lab2.py
Does not alter NMEA inputs.
"""
from pathlib import Path
import csv
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

BASE = Path(__file__).resolve().parents[1]
SRC = BASE / 'analysis/results/epochs.csv'
OUT = BASE / 'analysis/plots'
OUT.mkdir(parents=True, exist_ok=True)
NAMES = ['open_standalone','open_rtk','occluded_standalone','occluded_rtk','walking_rtk']
LABELS = {'open_standalone':'Open standalone','open_rtk':'Open RTK', 'occluded_standalone':'Occluded standalone','occluded_rtk':'Occluded RTK','walking_rtk':'Walking RTK'}
rows = {name:[] for name in NAMES}
with SRC.open(newline='') as f:
    for r in csv.DictReader(f):
        if r['dataset'] not in rows: continue
        row={'time':r['time_utc'],'quality':int(r['fix_quality'])}
        for inp,out in [('easting_m','e'),('northing_m','n'),('altitude_m','h')]:
            try: row[out]=float(r[inp])
            except (ValueError, TypeError): row[out]=float('nan')
        rows[r['dataset']].append(row)

def arr(name, field, valid=True):
    data=rows[name]
    if valid:
        data=[r for r in data if np.isfinite(r['e']) and np.isfinite(r['n'])]
    return np.asarray([r[field] for r in data])

def relative(name):
    e,n=arr(name,'e'),arr(name,'n')
    return e-e.mean(),n-n.mean()

def save(fig, file):
    fig.savefig(OUT/file, dpi=220, bbox_inches='tight')
    plt.close(fig)
    print('Saved:',OUT/file)

# 1/2: matched-scale overlays, each dataset relative to its own centroid
PLOTS=[('01_open_scatter.png', ['open_standalone','open_rtk'], 'Plot 1 · Open sky: centroid-relative coordinates'),
       ('02_occluded_scatter.png',['occluded_standalone','occluded_rtk'],'Plot 2 · Occluded: centroid-relative coordinates')]
maxabs=0.0
for names in (PLOTS[0][1], PLOTS[1][1]):
    for name in names:
        x,y=relative(name)
        maxabs=max(maxabs,np.max(np.abs(x)),np.max(np.abs(y)))
lim=max(1.0,maxabs*1.05)
print('Scatter plot matched limits: ±%.3f m'%lim)
for filename, names, title in PLOTS:
    # Main panels use identical limits and true equal scale for comparison.
    # Separate zoom panels sit OUTSIDE the main plot, so no data are hidden.
    fig = plt.figure(figsize=(12, 7.5), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.7, 1.0], wspace=.12, hspace=.25)
    ax = fig.add_subplot(gs[:, 0])
    styles = [('o', 'tab:blue'), ('x', 'tab:orange')]
    for name, (marker, color) in zip(names, styles):
        x, y = relative(name)
        ax.scatter(x, y, s=12, alpha=.65, marker=marker,
                   label=f'{LABELS[name]} (n={len(x)})', color=color)
    ax.set(xlabel='Relative Easting (m)', ylabel='Relative Northing (m)',
           title=title, xlim=(-lim, lim), ylim=(-lim, lim))
    ax.set_aspect('equal', adjustable='box')
    ax.grid(alpha=.2)
    ax.legend(loc='upper left', fontsize=9)

    if filename.startswith('01_'):
        zooms = [('open_standalone', 1.0, 'Standalone detail (±1 m)'),
                 ('open_rtk', .05, 'RTK fixed detail (±0.05 m)')]
    else:
        zooms = [('occluded_rtk', 15.0, 'RTK detail (±15 m)'),
                 ('occluded_rtk', 5.0, 'RTK center detail (±5 m)')]
    for i, (focus_name, radius, caption) in enumerate(zooms):
        zoom_ax = fig.add_subplot(gs[i, 1])
        marker, color = styles[names.index(focus_name)]
        x, y = relative(focus_name)
        zoom_ax.scatter(x, y, s=13, alpha=.7, marker=marker, color=color)
        zoom_ax.set(xlim=(-radius, radius), ylim=(-radius, radius),
                    title=caption, xlabel='Relative Easting (m)',
                    ylabel='Relative Northing (m)')
        zoom_ax.set_aspect('equal', adjustable='box')
        zoom_ax.grid(alpha=.2)
        zoom_ax.tick_params(labelsize=8)
    save(fig, filename)

# 3: histograms (2x2 subplots)
fig,axs=plt.subplots(2,2,figsize=(10,8),constrained_layout=True)
for ax,name in zip(axs.flat,NAMES[:4]):
    x,y=relative(name);distance=np.hypot(x,y)
    ax.hist(distance,bins=32,edgecolor='white',alpha=.85)
    ax.set(title=LABELS[name],xlabel='Distance from centroid (m)',ylabel='Epoch count')
    ax.grid(alpha=.2)
fig.suptitle('Plot 3 · Distance-from-centroid distributions')
save(fig,'03_distance_histograms.png')

# 4: all 5 altitudes as separate lines; time relative to each run start
def time_seconds(t):
    try:
        return int(t[:2])*3600+int(t[2:4])*60+float(t[4:])
    except (ValueError,TypeError): return float('nan')
fig,ax=plt.subplots(figsize=(10,6))
for name in NAMES:
    d=[r for r in rows[name] if np.isfinite(r['h']) and np.isfinite(r['e']) and np.isfinite(r['n'])]
    t=np.array([time_seconds(r['time']) for r in d]);h=np.array([r['h'] for r in d]);
    if len(t): ax.plot((t-t[0])/60,h-np.mean(h),label=LABELS[name],linewidth=1.2)
ax.set(xlabel='Time since run start (minutes)',ylabel='Altitude minus run mean (m)',title='Plot 4 · Altitude variation over time')
ax.grid(alpha=.2);ax.legend()
save(fig,'04_altitude_vs_time.png')

# 5: 3 quality time series (no fabrication of time-to-first-fix)
fig,axs=plt.subplots(3,1,figsize=(11,7.8),sharey=True,constrained_layout=True)
for ax,name in zip(axs,['open_rtk','occluded_rtk','walking_rtk']):
    d=rows[name]; t=np.array([time_seconds(r['time']) for r in d]);q=np.array([r['quality'] for r in d]);tt=(t-t[0])/60
    ax.step(tt,q,where='post',label=LABELS[name]);ax.set(ylabel='Fix quality',ylim=(-.3,5.5));ax.set_yticks([0,1,2,4,5]);ax.grid(alpha=.2);ax.legend(loc='upper right')
    if name=='open_rtk':
        fixed=np.flatnonzero(q==4)
        if len(fixed):
            x=float(tt[fixed[0]])
            ax.axvline(x,color='black',linestyle='--',alpha=.65)
            ax.annotate(f'First observed fixed epoch: +{x*60:.0f} s\n(not time-to-first-fix since corrections enabled)',
                        (x,4),xytext=(15,-48),textcoords='offset points',fontsize=8,
                        arrowprops=dict(arrowstyle='->',lw=.8))
axs[-1].set_xlabel('Time since recorded segment start (minutes)')
fig.suptitle('Plot 5 · Fix quality versus time')
save(fig,'05_fix_quality_vs_time.png')

# 6: TLS line and quality-specific classes
name='walking_rtk';valid=[r for r in rows[name] if np.isfinite(r['e']) and np.isfinite(r['n'])]
points=np.array([[r['e'],r['n']] for r in valid]); center=points.mean(axis=0)
_,_,v=np.linalg.svd(points-center,full_matrices=False); direction=v[0]
t=(points-center)@direction; fitted=center+np.outer(np.linspace(t.min(),t.max(),300),direction)
fig, ax = plt.subplots(figsize=(8, 9))
colors = {0:'gray', 1:'tab:red', 2:'tab:orange', 4:'tab:green', 5:'tab:blue'}
for quality in sorted(set(r['quality'] for r in valid)):
    ii = np.array([i for i, r in enumerate(valid) if r['quality'] == quality])
    ax.scatter(points[ii,0]-points[0,0], points[ii,1]-points[0,1],
               s=18, alpha=.8, color=colors.get(quality,'black'),
               label=f'Quality {quality} (n={len(ii)})')
ax.plot(fitted[:,0]-points[0,0], fitted[:,1]-points[0,1],
        color='black', lw=1.5, label='Total least-squares best-fit line')
perp = (points-center) @ v[1]
rmse = np.sqrt(np.mean(perp**2))
ax.set(xlabel='Relative Easting (m)', ylabel='Relative Northing (m)',
       title=f'Plot 6 · Walking: best-fit line\n(perpendicular RMSE {rmse:.3f} m)')
ax.set_aspect('equal', adjustable='box')
ax.grid(alpha=.2)
# Place legend below the axes rather than obscuring the narrow walking route.
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=3, fontsize=9,
           bbox_to_anchor=(.5, .015), frameon=True)
fig.subplots_adjust(left=.20, right=.86, top=.89, bottom=.18)
save(fig, '06_walking_best_fit.png')
print('Done: 6 plots created; verify labels and inset visually before submission.')
