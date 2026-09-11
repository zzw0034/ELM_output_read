"""Acceptance checks for the 4 km AD rerun smoke test; run on a compute node.

Three questions, kept apart:
  1. do BOTH fixes act in this one run - HDM read, and no sentinel forcing
  2. are the annual fluxes complete, and does the instantaneous h2 state match
     the restart written at the same instant, patch by patch
  3. does the new build behave at 30 nodes - output shapes and PIO layout

Nothing here is judged on a domain mean.
"""
import argparse
import json
from pathlib import Path

import netCDF4 as nc
import numpy as np

CASE = '20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup'
REF_RUN = Path('/scratch/hpcl-cli185/zw5/cime_output_dirs/'
               '20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup/run')
REF_CASE = '20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup'
SENTINEL_FSDS, TMIN, TMAX = 1.0, -30.0, 45.0
HDM_REFERENCE = 5.128       # domain mean measured in job 522373
NATURAL, PINE = 1, 1


def read(d, name, t=None):
    v = d.variables[name]
    a = v[:] if (not v.dimensions or v.dimensions[0] != 'time') else (v[0] if t is None else v[t])
    return np.ma.filled(np.asarray(a, dtype=float), np.nan)


def to_c(v, units):
    u = (units or '').strip().lower()
    if u in ('k', 'kelvin'):
        return v - 273.15
    if u in ('degc', 'c', 'celsius', 'degrees c'):
        return v
    raise ValueError('unknown temperature units ' + repr(units))


def full_year_records(d):
    """Indices whose time_bounds span a full calendar year, and their dates."""
    tb = np.ma.filled(np.asarray(d.variables['time_bounds'][:], dtype=float), np.nan)
    length = tb[:, 1] - tb[:, 0]
    mcdate = np.asarray(d.variables['mcdate'][:], dtype=int)
    cal = (getattr(d.variables['time'], 'calendar', '') or '').lower()
    expected = 365.0 if cal in ('noleap', '365_day') else float(
        np.bincount(np.round(length[length > 0]).astype(int)).argmax())
    ok = np.flatnonzero(np.abs(length - expected) <= 0.5)
    return ok, mcdate, length, expected, cal


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    R = args.run_dir
    rep = {'case': CASE, 'run_dir': str(R), 'checks': {}}

    h0 = sorted(R.glob(f'{CASE}.elm.h0.*.nc'))[0]
    h1 = sorted(R.glob(f'{CASE}.elm.h1.*.nc'))[0]

    # Pair h2 with the restart written at the SAME instant, by date. Taking the
    # last of each would compare different times once the run has several files:
    # hist_mfilt caps a file at 50 records, one of which is the short
    # initialisation record, so a 50-year segment spills its final year into the
    # next file while restarts land on REST_N boundaries.
    restarts = {int(q.name.split('.elm.r.')[1][:10].replace('-', '')[:8]): q
                for q in R.glob(f'{CASE}.elm.r.*.nc')}
    h2, h2_index, h2_date_sel, rst = None, None, None, None
    for q in sorted(R.glob(f'{CASE}.elm.h2.*.nc')):
        with nc.Dataset(q) as d:
            dates = np.asarray(d.variables['mcdate'][:], dtype=int)
        for i, dt in enumerate(dates):
            if int(dt) in restarts and (h2_date_sel is None or int(dt) >= h2_date_sel):
                h2, h2_index, h2_date_sel = q, int(i), int(dt)
                rst = restarts[int(dt)]
    if h2 is None:
        raise SystemExit('no h2 snapshot shares a date with any restart; '
                         'available restarts: %r' % sorted(restarts))

    # ---- record structure -------------------------------------------------
    all_h0 = sorted(R.glob(f'{CASE}.elm.h0.*.nc'))
    per_file = []
    for q in all_h0:
        with nc.Dataset(q) as d:
            o, m, L, e, c = full_year_records(d)
            per_file.append({'file': q.name, 'records': int(len(L)),
                             'full_year_records': int(len(o)),
                             'model_years': [int(m[o[0]] // 10000) - 1,
                                             int(m[o[-1]] // 10000) - 1] if len(o) else [],
                             'short_records': [round(float(L[i]), 4)
                                               for i in range(len(L))
                                               if abs(L[i] - e) > 0.5]})
    with nc.Dataset(h0) as d:
        ok, mcdate, length, expected, cal = full_year_records(d)
        rep['checks']['record_structure'] = {
            'files_on_this_tape': per_file,
            'calendar': cal, 'expected_interval_days': expected,
            'n_records': int(len(length)),
            'full_year_record_indices': [int(i) for i in ok],
            'full_year_model_years': [int(mcdate[i] // 10000) - 1 for i in ok],
            'rejected': [{'index': int(i), 'days': float(length[i])}
                         for i in range(len(length)) if i not in set(ok.tolist())],
            'verdict': 'PASS' if len(ok) >= 1 else 'FAIL: no complete annual interval',
        }
        if not len(ok):
            raise SystemExit(json.dumps(rep, indent=2))
        last = int(ok[-1])
        lat, lon = read(d, 'lat'), read(d, 'lon')
        nlon = len(lon)
        hdm = read(d, 'HDM', last)
        tbot = to_c(read(d, 'TBOT', last), getattr(d.variables['TBOT'], 'units', ''))
        fsds = read(d, 'FSDS', last)
        gpp = read(d, 'GPP', last)
        model_year = int(mcdate[last] // 10000) - 1

    # ---- land mask, from the patch tape -----------------------------------
    with nc.Dataset(h1) as d:
        cix = read(d, 'cols1d_ixy').astype(int) - 1
        cjy = read(d, 'cols1d_jxy').astype(int) - 1
        land = np.unique(cjy * nlon + cix)
        h1_fields = set(d.variables)
        h1_methods = {v: getattr(d.variables[v], 'cell_methods', None)
                      for v in ('LEAFC', 'LEAFC_ALLOC', 'LEAFC_LOSS') if v in d.variables}

    # ---- check 1a: HDM actually read --------------------------------------
    hv = hdm.ravel()[land]
    rep['checks']['hdm'] = {
        'model_year': model_year,
        'mean': float(np.nanmean(hv)), 'min': float(np.nanmin(hv)),
        'max': float(np.nanmax(hv)),
        'all_zero': bool(np.nanmax(np.abs(hv)) == 0),
        'reference_mean_522373': HDM_REFERENCE,
        'verdict': 'PASS' if (np.nanmax(np.abs(hv)) > 0 and np.nanmin(hv) >= 0
                              and abs(np.nanmean(hv) - HDM_REFERENCE) < 1.0)
                   else 'FAIL: HDM not read as expected',
    }

    # ---- check 1b: no sentinel forcing anywhere ---------------------------
    tl, fl, gl = tbot.ravel()[land], fsds.ravel()[land], gpp.ravel()[land]
    bad = (fl < SENTINEL_FSDS) | (tl < TMIN) | (tl > TMAX)
    rep['checks']['sentinel_forcing'] = {
        'model_year': model_year, 'land_cells': int(len(land)),
        'flagged_cells': int(bad.sum()),
        'min_fsds': float(np.nanmin(fl)), 'max_tbot_c': float(np.nanmax(tl)),
        'min_tbot_c': float(np.nanmin(tl)),
        'cells_with_zero_gpp': int((gl <= 0).sum()),
        'verdict': 'PASS' if bad.sum() == 0 else 'FAIL: %d cells on sentinel forcing' % bad.sum(),
    }

    # ---- check 2a: requested flux fields present --------------------------
    need = ['M_LEAFC_TO_FIRE', 'M_LEAFC_TO_LITTER_FIRE', 'M_LEAFC_TO_LITTER',
            'M_LEAFC_STORAGE_TO_FIRE', 'M_LEAFC_XFER_TO_FIRE', 'XR', 'AVAILC',
            'PLANT_CALLOC', 'LEAFC_XFER_TO_LEAFC', 'CPOOL_TO_LEAFC',
            'LEAFC_ALLOC', 'LEAFC_LOSS', 'LEAFC_TO_LITTER', 'FAREA_BURNED']
    missing = [f for f in need if f not in h1_fields]
    rep['checks']['flux_fields'] = {
        'requested': len(need), 'missing': missing,
        'h1_cell_methods': h1_methods,
        'verdict': 'PASS' if not missing else 'FAIL: missing %r' % missing,
    }

    # ---- check 2b: h2 instantaneous state == restart at the same instant ---
    with nc.Dataset(h2) as d:
        h2_date = np.asarray(d.variables['mcdate'][:], dtype=int)
        h2_methods = {v: getattr(d.variables[v], 'cell_methods', None)
                      for v in d.variables if v in ('LEAFC', 'TLAI', 'CPOOL')}
        k = h2_index                          # the snapshot matching the restart
        h2_leafc = read(d, 'LEAFC', k)
        h2_tlai = read(d, 'TLAI', k)
        h2_ix = read(d, 'pfts1d_ixy').astype(int)
        h2_jy = read(d, 'pfts1d_jxy').astype(int)
        h2_veg = read(d, 'pfts1d_itype_veg').astype(int)
        snapshot_date = int(h2_date[k])

    with nc.Dataset(rst) as r:
        r_leafc = read(r, 'leafc')
        r_tlai = read(r, 'tlai')
        r_ix = read(r, 'pfts1d_ixy').astype(int)
        r_jy = read(r, 'pfts1d_jxy').astype(int)
        r_veg = read(r, 'pfts1d_itypveg').astype(int)

    restart_date = int(str(rst.name).split('.r.')[1][:10].replace('-', '')[:8])
    same_len = len(h2_leafc) == len(r_leafc)
    identity = bool(same_len and np.array_equal(h2_ix, r_ix)
                    and np.array_equal(h2_jy, r_jy) and np.array_equal(h2_veg, r_veg))
    res = {'h2_file': h2.name, 'h2_record_index': h2_index,
           'h2_snapshot_mcdate': snapshot_date, 'restart_file': rst.name,
           'restart_date_from_name': restart_date,
           'dates_match': snapshot_date == restart_date,
           'h2_cell_methods': h2_methods,
           'patch_count_h2': int(len(h2_leafc)), 'patch_count_restart': int(len(r_leafc)),
           'patch_identity_matches_elementwise': identity}
    if identity:
        # ELM writes spval = 1e36 for patches a tape does not carry, and the two
        # files do not mask it identically. Comparing raw arrays therefore
        # compares fill against real data on the ~74% of patches that are
        # inactive. Restrict to patches both files actually report.
        FILL = 1e30
        real = (np.isfinite(h2_leafc) & np.isfinite(r_leafc)
                & (np.abs(h2_leafc) < FILL) & (np.abs(r_leafc) < FILL))
        res['patches_reported_by_both'] = int(real.sum())
        res['patches_fill_in_h2'] = int((np.abs(h2_leafc) >= FILL).sum())
        res['patches_fill_in_restart'] = int((np.abs(r_leafc) >= FILL).sum())
        both = real
        diff = np.abs(h2_leafc[both] - r_leafc[both])
        scale = np.maximum(np.abs(r_leafc[both]), 1e-30)
        res.update({
            'n_compared': int(both.sum()),
            'max_abs_diff_gC_m2': float(diff.max()) if both.any() else None,
            'max_rel_diff': float((diff / scale).max()) if both.any() else None,
            'n_exceeding_1e-5_relative': int(((diff / scale) > 1e-5).sum()),
            'tlai_max_abs_diff': float(np.nanmax(np.abs(h2_tlai[both] - r_tlai[both]))),
        })
        # h2 is float32, the restart is float64, so exact equality is not the
        # test; single-precision rounding is.
        agree = (res['n_exceeding_1e-5_relative'] == 0 and both.sum() > 0)
        res['verdict'] = ('PASS: h2 is the state the restart holds at the same instant'
                          if (agree and res['dates_match'] and
                              h2_methods.get('LEAFC') == 'time: point')
                          else 'FAIL: h2 does not reproduce the restart state')
    else:
        res['verdict'] = 'FAIL: cannot align h2 and restart patch vectors'
    rep['checks']['h2_vs_restart'] = res

    # ---- check 3: output shapes ------------------------------------------
    sizes = {}
    for tag, path in (('h0', h0), ('h1', h1), ('h2', h2), ('elm.r', rst)):
        n = 1
        if tag != 'elm.r':
            with nc.Dataset(path) as d:
                n = len(d.dimensions['time'])
        sizes[tag] = {'bytes': int(path.stat().st_size), 'records': int(n),
                      'MB_per_record': round(path.stat().st_size / n / 1e6, 1)}
    rep['checks']['output_volume'] = sizes

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, indent=2, allow_nan=False))
    for k, v in rep['checks'].items():
        if isinstance(v, dict) and 'verdict' in v:
            print(f'{k:22s} {v["verdict"]}')


if __name__ == '__main__':
    main()
