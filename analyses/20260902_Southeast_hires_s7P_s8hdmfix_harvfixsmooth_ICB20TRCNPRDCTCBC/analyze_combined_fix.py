"""Combined-fix outcome from the production AD rerun; run on a compute node.

The first run with the corrected HDM reader AND the repaired zone_mappings.
Reads every closed segment file on each tape (glob + MFDataset), concatenated
along the record dimension. The caller is responsible for only pointing this
at a run whose segments are all finished — do not run it while a later
segment is still writing to the same tape.

Three deliverables, kept apart:
  A. per-PFT low-LAI fractions, split three ways and reported by region,
     never as a single domain number
  B. the 405 residual and 193 sentinel populations, tracked by location
  C. the leaf carbon budget, closed on year-end state from the h2 tape, with
     fire separated from background mortality using fields that job 522626
     did not carry

Group membership is retrospective, defined by the final state of job 522373,
a different simulation. That is a controlled comparison of the same locations,
not an independent sample.
"""
import argparse
import csv
import json
from pathlib import Path

import netCDF4 as nc
import numpy as np

SECONDS_YEAR = 365 * 86400.0
LOW_LAI, ZERO_LEAFC = 0.5, 1e-6
NATURAL, PINE, BES = 1, 1, 9        # BES resolved from clm_params at runtime
MIN_WEIGHT = 0.05
REF_CASE = '20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup'
REF_WINDOW = 81


def read(d, name, t=None):
    v = d.variables[name]
    a = v[:] if (not v.dimensions or v.dimensions[0] != 'time') else (v[0] if t is None else v[t])
    return np.ma.filled(np.asarray(a, dtype=float), np.nan)


def records(d):
    """Model year of each record and whether it spans a full calendar year."""
    tb = np.ma.filled(np.asarray(d.variables['time_bounds'][:], dtype=float), np.nan)
    length = tb[:, 1] - tb[:, 0]
    mc = np.asarray(d.variables['mcdate'][:], dtype=int)
    cal = (getattr(d.variables['time'], 'calendar', '') or '').lower()
    exp = 365.0 if cal in ('noleap', '365_day') else float(
        np.bincount(np.round(length[length > 0]).astype(int)).argmax())
    return (mc // 10000) - 1, np.abs(length - exp) <= 0.5, mc


def stats(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if not a.size:
        return {'n': 0}
    return {'n': int(a.size), 'mean': float(a.mean()), 'median': float(np.median(a)),
            'p25': float(np.quantile(a, .25)), 'p75': float(np.quantile(a, .75))}


def classify(lai, leafc, weight):
    """Three classes, never one. Weighted by patch area within the population."""
    ok = np.isfinite(lai) & np.isfinite(leafc) & (weight > 0)
    n = int(ok.sum())
    if not n:
        return {'n': 0}
    lai, leafc = lai[ok], leafc[ok]
    zero = leafc <= ZERO_LEAFC
    low_alive = (~zero) & (lai < LOW_LAI)
    healthy = lai >= LOW_LAI
    return {'n': n,
            'frac_zero_leafc': round(float(zero.mean()), 5),
            'frac_low_lai_but_alive': round(float(low_alive.mean()), 5),
            'frac_healthy': round(float(healthy.mean()), 5),
            'median_lai': round(float(np.median(lai)), 4),
            'mean_leafc': round(float(leafc.mean()), 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--case', required=True)
    ap.add_argument('--ref-run', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--max-year', type=int, default=None,
                    help='ignore records beyond this model year')
    a = ap.parse_args()

    h1_files = sorted(a.run_dir.glob(f'{a.case}.elm.h1.*-01-01-00000.nc'))
    h0_files = sorted(a.run_dir.glob(f'{a.case}.elm.h0.*-01-01-00000.nc'))
    h2_files = sorted(a.run_dir.glob(f'{a.case}.elm.h2.*-01-01-00000.nc'))
    for tag, files in (('h0', h0_files), ('h1', h1_files), ('h2', h2_files)):
        if not files:
            raise SystemExit(f'no {tag} segment files found under {a.run_dir}')
    h1, h0, h2 = h1_files, h0_files, h2_files
    rep = {'case': a.case,
          'files': {'h0': [p.name for p in h0], 'h1': [p.name for p in h1],
                    'h2': [p.name for p in h2]},
          'caveats': [
        'All closed segment files on each tape are read and concatenated by '
        'record; the caller must not point this at a run with a segment still '
        'writing.',
        'Group membership comes from the final state of job 522373, a different '
        'simulation, so it is a retrospective comparison of the same locations.',
        'Fire association is not causation; the leaf budget gives the proximate '
        'loss term, not the trigger.',
    ]}

    # ---- populations, from the reference experiment -----------------------
    with nc.Dataset(a.ref_run / f'{REF_CASE}.elm.h1.{REF_WINDOW:04d}-01-01-00000.nc') as d, \
         nc.Dataset(a.ref_run / f'{REF_CASE}.elm.h0.{REF_WINDOW:04d}-01-01-00000.nc') as g:
        rlon = read(d, 'lon'); rnlon = len(rlon)
        rix = read(d, 'pfts1d_ixy').astype(int) - 1
        rjy = read(d, 'pfts1d_jxy').astype(int) - 1
        rwt = read(d, 'pfts1d_wtgcell')
        rlai = read(d, 'TLAI')
        sel = ((read(d, 'pfts1d_itype_veg') == PINE)
               & (read(d, 'pfts1d_itype_lunit') == NATURAL)
               & (rwt > MIN_WEIGHT) & np.isfinite(rlai))
        ids = np.flatnonzero(sel)
        rkey = rjy[ids] * rnlon + rix[ids]
        tbot = read(g, 'TBOT'); fsds = read(g, 'FSDS')
        u = getattr(g.variables['TBOT'], 'units', '')
        tb = (tbot - 273.15 if u.lower() in ('k', 'kelvin') else tbot).ravel()[rkey]
        fs = fsds.ravel()[rkey]
        low = rlai[ids] < LOW_LAI
        sentinel_key = rkey[low & (fs < 1) & (tb > 45)]
        residual_key = rkey[low & ~((fs < 1) & (tb > 45))]
        healthy_key = rkey[rlai[ids] > 1.5]
    rng = np.random.default_rng(0)
    healthy_key = np.sort(rng.choice(healthy_key, size=min(2000, healthy_key.size),
                                     replace=False))
    rep['populations'] = {'residual': int(residual_key.size),
                          'sentinel': int(sentinel_key.size),
                          'healthy_sample': int(healthy_key.size)}

    # ---- production run geometry -----------------------------------------
    with nc.MFDataset(h1) as d:
        nlon = len(read(d, 'lon'))
        lat, lon = read(d, 'lat'), read(d, 'lon')
        pix = read(d, 'pfts1d_ixy').astype(int) - 1
        pjy = read(d, 'pfts1d_jxy').astype(int) - 1
        pkey = pjy * nlon + pix
        pveg = read(d, 'pfts1d_itype_veg').astype(int)
        plun = read(d, 'pfts1d_itype_lunit').astype(int)
        pwt = read(d, 'pfts1d_wtgcell')
        years, full, mc = records(d)
        col_key = (read(d, 'cols1d_jxy').astype(int) - 1) * nlon + read(d, 'cols1d_ixy').astype(int) - 1
        col_wt = read(d, 'cols1d_wtgcell')
        col_nat = read(d, 'cols1d_itype_lunit') == NATURAL
    if a.max_year:
        full &= years <= a.max_year
    idx = np.flatnonzero(full)
    rep['model_years'] = [int(years[idx[0]]), int(years[idx[-1]])]

    plat = lat[pkey // nlon]
    natural = (plun == NATURAL) & (pwt > 0)
    regions = {'whole_domain': natural,
               'florida_box': natural & (plat <= 31.0) & (lon[pkey % nlon] >= -87.6),
               'south_of_26N': natural & (plat < 26.0)}

    # ---- A. per-PFT classification, by 20-year window and region ----------
    windows = []
    lo = int(years[idx[0]])
    while lo <= int(years[idx[-1]]):
        hi = min(lo + 19, int(years[idx[-1]]))
        sel = [i for i in idx if lo <= years[i] <= hi]
        if sel:
            windows.append((lo, hi, sel))
        lo = hi + 1

    per_pft = {}
    with nc.MFDataset(h1) as d:
        for lo, hi, sel in windows:
            lai_sum = np.zeros(len(pkey)); lc_sum = np.zeros(len(pkey))
            for t in sel:
                lai_sum += np.nan_to_num(read(d, 'TLAI', t))
                lc_sum += np.nan_to_num(read(d, 'LEAFC', t))
            lai_m, lc_m = lai_sum / len(sel), lc_sum / len(sel)
            w = {}
            for rname, rmask in regions.items():
                per_v = {}
                for v in np.unique(pveg[rmask]):
                    m = rmask & (pveg == v)
                    if m.sum() >= 20:
                        per_v[int(v)] = classify(lai_m[m], lc_m[m], pwt[m])
                w[rname] = per_v
            per_pft[f'{lo}-{hi}'] = w
    rep['per_pft_by_window_and_region'] = per_pft

    # ---- B and C. tracked groups, annual, with the leaf budget ------------
    groups = {'residual': residual_key, 'sentinel': sentinel_key,
              'healthy_sample': healthy_key}
    pine_sel = (pveg == PINE) & (plun == NATURAL) & (pwt > MIN_WEIGHT)
    pine_ids = np.flatnonzero(pine_sel)
    pine_key = pkey[pine_ids]
    order = np.argsort(pine_key)
    pine_ids, pine_key = pine_ids[order], pine_key[order]
    gidx = {}
    for name, keys in groups.items():
        pos = np.searchsorted(pine_key, keys)
        pos = pos[(pos < pine_key.size)]
        pos = pos[pine_key[pos] == keys[:pos.size]] if pos.size else pos
        gidx[name] = np.unique(pos)
    take = np.unique(np.concatenate([v for v in gidx.values() if v.size]))
    rows = pine_ids[take]
    local = {k: np.searchsorted(take, v) for k, v in gidx.items()}
    rep['tracked_matched'] = {k: int(v.size) for k, v in gidx.items()}

    flux = ('LEAFC_ALLOC', 'LEAFC_LOSS', 'LEAFC_TO_LITTER', 'M_LEAFC_TO_LITTER',
            'M_LEAFC_TO_FIRE', 'M_LEAFC_TO_LITTER_FIRE', 'GPP', 'NPP', 'XR',
            'AVAILC', 'CPOOL', 'BTRAN', 'TLAI', 'LEAFC')
    # FAREA_BURNED is registered on the COLUMN, in CNStateType.F90, not on the
    # patch. Reading it with the patch index silently walks off the end.
    colf = ('FPG', 'FPI', 'COL_FIRE_CLOSS', 'FAREA_BURNED')
    size = len(lat) * nlon
    series = {}
    with nc.MFDataset(h1) as d, nc.MFDataset(h2) as s:
        s_years, s_full, s_mc = records(s)
        # h2 record stamped (y+1)-01-01 is the state at the END of year y.
        end_state = {int(m // 10000) - 1: i for i, m in enumerate(s_mc)}
        for t in idx:
            y = int(years[t])
            rec = {'year': y}
            for f in flux:
                rec[f] = read(d, f, t)[rows]
            for f in colf:
                v = read(d, f, t)
                ok = np.isfinite(v) & (col_wt > 0) & col_nat
                den = np.bincount(col_key[ok], weights=col_wt[ok], minlength=size)
                num = np.bincount(col_key[ok], weights=col_wt[ok] * v[ok], minlength=size)
                rec[f] = np.divide(num, den, out=np.full(size, np.nan), where=den > 0)[pine_key[take]]
            for tag, yy in (('state_end', y), ('state_start', y - 1)):
                j = end_state.get(yy)
                rec[tag] = read(s, 'LEAFC', j)[rows] if j is not None else None
            series[y] = rec

    out = {}
    for name, loc in local.items():
        if not loc.size:
            continue
        by_year, budget = {}, []
        for y in sorted(series):
            r = series[y]
            by_year[str(y)] = {f: stats(r[f][loc]) for f in
                               ('TLAI', 'LEAFC', 'GPP', 'NPP', 'XR', 'CPOOL', 'BTRAN',
                                'FPG', 'FAREA_BURNED', 'LEAFC_ALLOC', 'LEAFC_LOSS')}
            if r['state_end'] is not None and r['state_start'] is not None:
                d_state = r['state_end'][loc] - r['state_start'][loc]
                net = (r['LEAFC_ALLOC'][loc] - r['LEAFC_LOSS'][loc]) * SECONDS_YEAR
                loss = r['LEAFC_LOSS'][loc] * SECONDS_YEAR
                firec = (r['M_LEAFC_TO_FIRE'][loc] + r['M_LEAFC_TO_LITTER_FIRE'][loc]) * SECONDS_YEAR
                bg = r['M_LEAFC_TO_LITTER'][loc] * SECONDS_YEAR
                lit = r['LEAFC_TO_LITTER'][loc] * SECONDS_YEAR
                with np.errstate(invalid='ignore', divide='ignore'):
                    share = np.where(loss > 0, firec / loss, np.nan)
                budget.append({
                    'year': y,
                    'delta_state_gC_m2': stats(d_state),
                    'net_flux_gC_m2': stats(net),
                    'closure_residual_gC_m2': stats(d_state - net),
                    'total_loss_gC_m2': stats(loss),
                    'fire_loss_gC_m2': stats(firec),
                    'background_mortality_gC_m2': stats(bg),
                    'litterfall_gC_m2': stats(lit),
                    'fire_share_of_loss': stats(share),
                })
        out[name] = {'n': int(loc.size), 'by_year': by_year, 'leaf_budget': budget}
    rep['tracked'] = out

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=2, allow_nan=False))
    print(json.dumps({'model_years': rep['model_years'],
                      'populations': rep['populations'],
                      'matched': rep['tracked_matched']}, indent=1))


if __name__ == '__main__':
    main()
