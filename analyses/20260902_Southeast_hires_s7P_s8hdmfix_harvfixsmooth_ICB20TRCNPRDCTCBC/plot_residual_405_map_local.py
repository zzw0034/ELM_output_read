# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "matplotlib"]
# ///
"""Map the 405 residual pine patches against the 193 repaired coastal ones."""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = '/private/tmp/claude-502/-Users-zw5-ORNL-workplace-pathfinder/04ce30fd-0cef-48d9-8ce1-a2caad41da66/scratchpad/'
OUT = ('/Users/zw5/ORNL_workplace/pathfinder/ELM_output_read/analyses/'
       '20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/outputs/')

m = np.load(D + 'seus_mask.npz')
lat, lon, land, pine = m['lat'], m['lon'], m['land'], m['pine']

res = np.array([[float(r['lat']), float(r['lon'])] for r in
                csv.DictReader(open(OUT + 'residual_pine_fire_522677/residual_trajectory.csv'))])
res = np.unique(res, axis=0)
sen = np.loadtxt(D + 'sentinel_cells.csv', delimiter=',', skiprows=1)

fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.2),
                         gridspec_kw={'width_ratios': [1.35, 1]})
for ax in axes:
    ax.set_facecolor('#eef3f7')
    ax.set_aspect(1 / np.cos(np.deg2rad(30)))
    ax.grid(alpha=.25, lw=.4, color='white')

LON, LAT = np.meshgrid(lon, lat)
for ax in axes:
    ax.scatter(LON[land], LAT[land], s=.30, c='#c9d3da', marker='s',
               linewidths=0, rasterized=True)
    ax.scatter(LON[pine], LAT[pine], s=.30, c='#a9c6a3', marker='s',
               linewidths=0, rasterized=True)

a = axes[0]
a.scatter(sen[:, 1], sen[:, 0], s=34, facecolor='none', edgecolor='#1f6fb4',
          linewidths=1.3, label='193 coastal cells, forcing repaired, now healthy')
a.scatter(res[:, 1], res[:, 0], s=15, c='#c1272d',
          label='405 residual cells, still declining')
a.set_xlim(lon.min(), lon.max()); a.set_ylim(lat.min(), lat.max())
a.set_title('SEUS 4 km domain', loc='left', fontsize=12)
a.legend(loc='upper right', fontsize=9, framealpha=.95, markerscale=1.4)

b = axes[1]
b.scatter(sen[:, 1], sen[:, 0], s=52, facecolor='none', edgecolor='#1f6fb4', linewidths=1.5)
b.scatter(res[:, 1], res[:, 0], s=30, c='#c1272d')
b.set_xlim(-86.2, -79.6); b.set_ylim(24.6, 31.4)
b.set_title('south Florida, where the 405 are', loc='left', fontsize=12)

for ax in axes:
    ax.set_xlabel('longitude'); ax.set_ylabel('latitude')
fig.suptitle('Pine patches still stranded after both fixes, model years 41-49 of the AD rerun',
             x=.007, ha='left', fontsize=13.5, weight='bold')
fig.text(.007, .015,
         'Grey: land. Green: gridcells carrying a pine patch above 5% weight. '
         'Group membership is defined by the final state of job 522373.\n'
         'The 405 sit where 1850 population density is about 0.05, against 4.16 for healthy pine, '
         'so the corrected HDM reader cannot suppress fire there.',
         fontsize=8.6, color='#333')
fig.tight_layout(rect=[0, .055, 1, .96])
fig.savefig(OUT + 'residual_405_map.png', dpi=170)
print('wrote', OUT + 'residual_405_map.png', '| residual', len(res), '| sentinel', len(sen))
