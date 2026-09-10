"""Read-only analysis of HDM-fixed AD residual pine; run on a compute node.

Fire is natural-landunit column loss mapped to gridcells, NOT pine leaf fire
loss. Windows are 20-year means, NOT event dates or end-of-year pool states.
No domain-sized model output is copied locally. Outputs are small tables/JSON.
"""
import argparse
import csv
import json
from pathlib import Path

import netCDF4 as nc
import numpy as np

CASE = '20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup'
DEFAULT_RUN = Path('/scratch/hpcl-cli185/zw5/cime_output_dirs') / CASE / 'run'
YEARS = (21, 41, 61, 81)
SECONDS_YEAR = 365 * 86400


def read(d, name):
    v = d.variables[name]
    a = v[0] if v.dimensions[0] == 'time' else v[:]
    return np.ma.filled(a.astype(float), np.nan)


def weighted_grid(d, name, prefix, size, nlon, natural=False):
    key = ((read(d, prefix + '_jxy').astype(int) - 1) * nlon
           + read(d, prefix + '_ixy').astype(int) - 1)
    w = read(d, prefix + '_wtgcell')
    val = read(d, name)
    ok = np.isfinite(val) & np.isfinite(w) & (w > 0)
    if natural:
        ok &= read(d, prefix + '_itype_lunit') == 1
    den = np.bincount(key[ok], weights=w[ok], minlength=size)
    num = np.bincount(key[ok], weights=w[ok] * val[ok], minlength=size)
    return np.divide(num, den, out=np.full(size, np.nan), where=den > 0)


def extract(path):
    with nc.Dataset(path) as d:
        lon, lat = read(d, 'lon'), read(d, 'lat')
        ix = read(d, 'pfts1d_ixy').astype(int) - 1
        jy = read(d, 'pfts1d_jxy').astype(int) - 1
        wt = read(d, 'pfts1d_wtgcell')
        lai = read(d, 'TLAI')
        mask = ((read(d, 'pfts1d_itype_veg') == 1)
                & (read(d, 'pfts1d_itype_lunit') == 1)
                & (wt > .05) & np.isfinite(lai))
        ids = np.flatnonzero(mask)
        key = jy[ids] * len(lon) + ix[ids]
        if len(np.unique(key)) != len(key):
            raise ValueError('Multiple selected pine patches per cell; do not silently overwrite')
        order = np.argsort(key)
        ids, key = ids[order], key[order]
        # Join by spatial IDs: parent pointers need not index the serialized
        # history topounit vector globally (e.g. processor-local pointers).
        result = dict(key=key, pft_index=ids, lon=lon[ix[ids]], lat=lat[jy[ids]],
                      weight=wt[ids])
        for name in ('TLAI', 'LEAFC', 'GPP', 'NPP', 'TOTVEGC', 'AR', 'MR', 'GR', 'CPOOL'):
            if name in d.variables:
                result[name] = read(d, name)[ids]
        for name in ('TBOT', 'FSDS'):
            result[name] = weighted_grid(d, name, 'topo1d',
                                         len(lat)*len(lon), len(lon))[key]
        units = getattr(d.variables['TBOT'], 'units', '')
        if units.lower() in ('k', 'kelvin'):
            result['TBOT'] -= 273.15
        elif units.lower() not in ('degc', 'c', 'degrees c', 'celsius'):
            raise ValueError('Unknown temperature units: ' + units)
        for name in ('COL_FIRE_CLOSS', 'FPG', 'FPG_P'):
            result[name] = weighted_grid(d, name, 'cols1d', len(lat)*len(lon),
                                         len(lon), natural=True)[key]
        result['fire_gC_m2_yr'] = result['COL_FIRE_CLOSS'] * SECONDS_YEAR
        # Denominator is gridcell natural vegetation, not pine alone.
        veg = weighted_grid(d, 'TOTVEGC', 'pfts1d', len(lat)*len(lon),
                            len(lon), natural=True)[key]
        result['natural_vegc'] = veg
        result['fire_over_mean_vegc'] = np.divide(
            result['fire_gC_m2_yr'], veg, out=np.full(len(key), np.nan), where=veg > 0)
        return result


def summary(a):
    a = a[np.isfinite(a)]
    return {'n': int(len(a)), 'mean': float(np.mean(a)) if len(a) else None,
            'median': float(np.median(a)) if len(a) else None,
            'p25': float(np.quantile(a, .25)) if len(a) else None,
            'p75': float(np.quantile(a, .75)) if len(a) else None}


def match_controls(base, final, residual):
    # Predefined 100-km and 1-degree-C calipers; 5 nearest eligible controls.
    # Reuse is allowed and reported. This controls geography/temperature only.
    candidates = np.flatnonzero((final['TLAI'] > 1.5) & (base['TLAI'] > .5)
                               & (final['FSDS'] > 1) & (final['TBOT'] < 45))
    pairs = []
    for i in np.flatnonzero(residual):
        dy = (base['lat'][candidates] - base['lat'][i]) * 111.2
        dx = ((base['lon'][candidates] - base['lon'][i]) * 111.2
              * np.cos(np.deg2rad(base['lat'][i])))
        dist = np.hypot(dx, dy)
        eligible = ((dist <= 100) &
                    (np.abs(base['TBOT'][candidates] - base['TBOT'][i]) <= 1))
        pos = np.flatnonzero(eligible)
        pos = pos[np.argsort(dist[pos])[:5]]
        pairs.extend((int(i), int(candidates[k]), float(dist[k])) for k in pos)
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=DEFAULT_RUN)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    data = {}
    sources = []
    for year in YEARS:
        path = args.run_dir / f'{CASE}.elm.h1.{year:04d}-01-01-00000.nc'
        data[year] = extract(path)
        sources.append({'path': str(path), 'bytes': path.stat().st_size})
        if not np.array_equal(data[year]['key'], data[21]['key']):
            raise ValueError('Selected patch identities differ across windows')
    final, base = data[81], data[21]
    low = final['TLAI'] < .5
    sentinel = low & (final['FSDS'] < 1) & (final['TBOT'] > 45)
    residual = low & ~sentinel
    healthy = (final['TLAI'] > 1.5) & (final['FSDS'] > 1)
    south = healthy & (final['lat'] >= 25.2) & (final['lat'] <= 30.1)
    pairs = match_controls(base, final, residual)
    matched = sorted(set(i for i, _, _ in pairs))
    report = {'sources': sources, 'counts': {
        'pine': len(low), 'low': int(low.sum()), 'sentinel': int(sentinel.sum()),
        'residual': int(residual.sum()), 'matched_residual': len(matched),
        'unique_controls': len(set(j for _, j, _ in pairs))}, 'windows': {},
        'caveats': ['20-year means cannot establish event timing or annual carbon closure.',
                    'Column fire is not pine leaf fire; ratio uses mean natural vegetation carbon.',
                    'Matching controls geography and temperature, not soil or moisture.',
                    'Final-state selection and surviving-control selection are retrospective.',
                    'Residual definition excludes the identified sentinel pattern, not every input error.']}
    metrics = ('TLAI', 'LEAFC', 'GPP', 'NPP', 'fire_gC_m2_yr',
               'fire_over_mean_vegc', 'FPG', 'FPG_P', 'TBOT', 'FSDS')
    for year, d in data.items():
        window = {}
        for label, mask in [('residual', residual), ('healthy_domain', healthy),
                            ('healthy_south', south)]:
            window[label] = {v: summary(d[v][mask]) for v in metrics}
        window['residual_low_count'] = int(np.sum(residual & (d['TLAI'] < .5)))
        window['matched_comparison'] = {}
        for v in metrics:
            target, controls = [], []
            for i in matched:
                js = [j for a, j, _ in pairs if a == i]
                target.append(d[v][i]); controls.append(np.nanmean(d[v][js]))
            target, controls = np.array(target), np.array(controls)
            window['matched_comparison'][v] = {
                'target': summary(target), 'control_mean_per_target': summary(controls),
                'paired_difference': summary(target-controls)}
        report['windows'][f'{year-20}-{year-1}'] = window
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / 'summary.json').open('w') as f:
        json.dump(report, f, indent=2, allow_nan=False)
    with (args.output_dir / 'residual_trajectory.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['key', 'pft_index', 'lat', 'lon', 'window_end', *metrics])
        for i in np.flatnonzero(residual):
            for year, d in data.items():
                w.writerow([int(d['key'][i]), int(d['pft_index'][i]), d['lat'][i],
                            d['lon'][i], year-1, *[d[v][i] for v in metrics]])
    with (args.output_dir / 'matched_controls.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['residual_key', 'control_key', 'distance_km'])
        w.writerows((int(final['key'][i]), int(final['key'][j]), dist) for i,j,dist in pairs)
    print(json.dumps(report['counts']))
    if report['counts']['residual'] != 405:
        print('WARNING: residual count differs from 405; reconcile masks before interpretation.')


if __name__ == '__main__':
    main()
