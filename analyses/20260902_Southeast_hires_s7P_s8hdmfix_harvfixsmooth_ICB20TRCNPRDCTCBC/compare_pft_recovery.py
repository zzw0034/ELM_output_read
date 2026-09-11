"""Why pine strands and broadleaf deciduous does not, in the SAME gridcells.

Both PFTs sit in the 405 residual gridcells and burn in the same fires. If
deciduous recovers and pine does not, the difference is the phenology pathway,
not the disturbance. The discriminating flux is LEAFC_XFER_TO_LEAFC, the
storage-to-leaf flush: CNEvergreenPhenology sets bgtr = 0 and has no onset
event, so an evergreen's leaves come only from current allocation, which needs
photosynthesis, which needs leaves.
"""
import argparse
import json
from pathlib import Path

import netCDF4 as nc
import numpy as np

SECONDS_YEAR = 365 * 86400.0
NATURAL, PINE, DECID = 1, 1, 7


def read(d, name, t=None):
    v = d.variables[name]
    a = v[:] if (not v.dimensions or v.dimensions[0] != 'time') else (v[0] if t is None else v[t])
    return np.ma.filled(np.asarray(a, dtype=float), np.nan)


def records(d):
    tb = np.ma.filled(np.asarray(d.variables['time_bounds'][:], dtype=float), np.nan)
    L = tb[:, 1] - tb[:, 0]
    mc = np.asarray(d.variables['mcdate'][:], dtype=int)
    return (mc // 10000) - 1, np.abs(L - 365.0) <= 0.5


def stats(a):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    return {'n': int(a.size), 'mean': float(a.mean()), 'median': float(np.median(a))} if a.size else {'n': 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--case', required=True)
    ap.add_argument('--cells', type=Path, required=True, help='CSV with a lat and lon column')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()

    import csv as _csv
    with a.cells.open() as f:
        rows = list(_csv.DictReader(f))
    want = sorted({(round(float(r['lat']), 4), round(float(r['lon']), 4)) for r in rows})

    h1 = a.run_dir / f'{a.case}.elm.h1.0001-01-01-00000.nc'
    with nc.Dataset(h1) as d:
        lat, lon = read(d, 'lat'), read(d, 'lon')
        nlon = len(lon)
        pix = read(d, 'pfts1d_ixy').astype(int) - 1
        pjy = read(d, 'pfts1d_jxy').astype(int) - 1
        pkey = pjy * nlon + pix
        pveg = read(d, 'pfts1d_itype_veg').astype(int)
        plun = read(d, 'pfts1d_itype_lunit').astype(int)
        pwt = read(d, 'pfts1d_wtgcell')
        years, full = records(d)

        lut = {(round(float(lat[k // nlon]), 4), round(float(lon[k % nlon]), 4)): k
               for k in np.unique(pkey)}
        keys = np.array(sorted({lut[w] for w in want if w in lut}))

        sel = {}
        for tag, v in (('pine', PINE), ('broadleaf_deciduous', DECID)):
            m = (plun == NATURAL) & (pveg == v) & (pwt > 0) & np.isin(pkey, keys)
            sel[tag] = np.flatnonzero(m)

        flds = ('TLAI', 'LEAFC', 'LEAFC_STORAGE', 'LEAFC_XFER', 'LEAFC_XFER_TO_LEAFC',
                'CPOOL_TO_LEAFC', 'LEAFC_ALLOC', 'M_LEAFC_TO_FIRE',
                'M_LEAFC_TO_LITTER_FIRE', 'GPP')
        out = {t: {} for t in sel}
        for i in np.flatnonzero(full):
            y = int(years[i])
            cache = {f: read(d, f, i) for f in flds}
            for tag, ids in sel.items():
                r = {}
                for f in flds:
                    v = cache[f][ids]
                    r[f] = stats(v * SECONDS_YEAR if f.endswith(('_TO_LEAFC', '_ALLOC',
                                                                 '_TO_FIRE', '_LITTER_FIRE'))
                                 or f == 'GPP' else v)
                out[tag][str(y)] = r

    rep = {'cells_requested': len(want), 'cells_found': int(keys.size),
           'patches': {t: int(v.size) for t, v in sel.items()},
           'units': 'states gC/m2; fluxes converted to gC/m2/yr',
           'by_year': out}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=2, allow_nan=False))
    print(json.dumps({k: rep[k] for k in ('cells_requested', 'cells_found', 'patches')}, indent=1))


if __name__ == '__main__':
    main()
