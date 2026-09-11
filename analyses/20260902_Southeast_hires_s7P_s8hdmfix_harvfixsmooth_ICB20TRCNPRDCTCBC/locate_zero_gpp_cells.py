"""Identify the land cells that still report GPP at or below zero.

Before the coastal mapping repair, 194 cells had GPP = 0 and every one was
explained by sentinel forcing. Four remain, with physical forcing, so that
explanation does not apply to them. This asks what they actually are rather
than assuming they are harmless.
"""
import argparse
import csv
import json
from pathlib import Path

import netCDF4 as nc
import numpy as np

NATURAL = 1


def read(d, name, t=None):
    v = d.variables[name]
    a = v[:] if (not v.dimensions or v.dimensions[0] != 'time') else (v[0] if t is None else v[t])
    return np.ma.filled(np.asarray(a, dtype=float), np.nan)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--h0', type=Path, required=True)
    ap.add_argument('--h1', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()

    with nc.Dataset(a.h0) as d:
        mcdate = np.asarray(d.variables['mcdate'][:], dtype=int)
        tb = np.ma.filled(np.asarray(d.variables['time_bounds'][:], dtype=float), np.nan)
        full = np.flatnonzero(np.abs((tb[:, 1] - tb[:, 0]) - 365.0) <= 0.5)
        t = int(full[-1])
        year = int(mcdate[t] // 10000) - 1
        lat, lon = read(d, 'lat'), read(d, 'lon')
        nlon = len(lon)
        gpp = read(d, 'GPP', t).ravel()
        tlai = read(d, 'TLAI', t).ravel()
        vegc = read(d, 'TOTVEGC', t).ravel()
        tbot = read(d, 'TBOT', t).ravel()
        fsds = read(d, 'FSDS', t).ravel()

    with nc.Dataset(a.h1) as d:
        cix = read(d, 'cols1d_ixy').astype(int) - 1
        cjy = read(d, 'cols1d_jxy').astype(int) - 1
        ckey = cjy * nlon + cix
        clun = read(d, 'cols1d_itype_lunit').astype(int)
        cwt = read(d, 'cols1d_wtgcell')
        pix = read(d, 'pfts1d_ixy').astype(int) - 1
        pjy = read(d, 'pfts1d_jxy').astype(int) - 1
        pkey = pjy * nlon + pix
        plun = read(d, 'pfts1d_itype_lunit').astype(int)
        pveg = read(d, 'pfts1d_itype_veg').astype(int)
        pwt = read(d, 'pfts1d_wtgcell')
        land = np.unique(ckey)

    size = len(lat) * nlon
    natveg = np.bincount(ckey[clun == NATURAL], weights=cwt[clun == NATURAL], minlength=size)
    # PFT 0 is bare ground in ELM's natural vegetation landunit.
    veg_pft = (plun == NATURAL) & (pveg > 0)
    vegetated = np.bincount(pkey[veg_pft], weights=pwt[veg_pft], minlength=size)
    bare = np.bincount(pkey[(plun == NATURAL) & (pveg == 0)],
                       weights=pwt[(plun == NATURAL) & (pveg == 0)], minlength=size)

    g = gpp[land]
    hit = land[(g <= 0) | ~np.isfinite(g)]
    rows = []
    for cell in hit:
        lus, wts = clun[ckey == cell], cwt[ckey == cell]
        rows.append({
            'cell_key': int(cell),
            'lat': float(lat[cell // nlon]), 'lon': float(lon[cell % nlon]),
            'gpp': float(gpp[cell]), 'tlai': float(tlai[cell]),
            'totvegc': float(vegc[cell]),
            'tbot': float(tbot[cell]), 'fsds': float(fsds[cell]),
            'natural_landunit_weight': float(natveg[cell]),
            'vegetated_pft_weight': float(vegetated[cell]),
            'bare_ground_weight': float(bare[cell]),
            'landunit_types_present': sorted(set(int(x) for x in lus)),
            'landunit_weights': [round(float(w), 4) for w in wts],
        })

    rep = {'h0': a.h0.name, 'model_year': year,
           'land_cells': int(len(land)), 'cells_with_gpp_le_zero': int(len(hit)),
           'landunit_code_note': '1=vegetated/natural, 2=crop, 3=UNUSED, 4=landice, '
                                 '5=deep lake, 6=wetland, 7-9=urban (elm_varcon)',
           'cells': rows}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=2, allow_nan=False))
    with (a.out.parent / 'zero_gpp_cells.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])) if rows else None
        if w:
            w.writeheader()
            for r in rows:
                w.writerow(r)
    print(json.dumps(rep, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
