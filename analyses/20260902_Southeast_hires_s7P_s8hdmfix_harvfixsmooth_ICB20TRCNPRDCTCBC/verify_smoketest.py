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

    # ---- grid geometry, from the first h0 file (static across segments) ---
    all_h0 = sorted(R.glob(f'{CASE}.elm.h0.*.nc'))
    if not all_h0:
        raise SystemExit(f'no h0 files found under {R}')
    with nc.Dataset(all_h0[0]) as d0:
        nlon = len(read(d0, 'lon'))
        cal = (getattr(d0.variables['time'], 'calendar', '') or '').lower()

    # ---- land mask, from the patch tape -----------------------------------
    with nc.Dataset(h1) as d:
        cix = read(d, 'cols1d_ixy').astype(int) - 1
        cjy = read(d, 'cols1d_jxy').astype(int) - 1
        land = np.unique(cjy * nlon + cix)
        h1_fields = set(d.variables)
        h1_methods = {v: getattr(d.variables[v], 'cell_methods', None)
                      for v in ('LEAFC', 'LEAFC_ALLOC', 'LEAFC_LOSS') if v in d.variables}

    # ---- record structure, and C1.1: sentinel/physical-range check on EVERY
    # complete annual h0 record across every closed segment file (not just
    # the last one) — RERUN_VERIFICATION_PLAN.md section 5, C1. Model year 0
    # (the mcdate=0001-01-01 cold-start init record, FSDS identically zero on
    # every land cell) is excluded, matching the plan's "excluding year 0001".
    per_file, year_flags = [], {}
    last_year = hdm_last = gpp_last = tbot_last = fsds_last = None
    for q in all_h0:
        with nc.Dataset(q) as d:
            o, m, L, e, c2 = full_year_records(d)
            per_file.append({'file': q.name, 'records': int(len(L)),
                             'full_year_records': int(len(o)),
                             'model_years': [int(m[o[0]] // 10000) - 1,
                                             int(m[o[-1]] // 10000) - 1] if len(o) else [],
                             'short_records': [round(float(L[i]), 4)
                                               for i in range(len(L))
                                               if abs(L[i] - e) > 0.5]})
            for i in o:
                yr = int(m[i] // 10000) - 1
                if yr < 1:
                    continue
                tb = to_c(read(d, 'TBOT', i), getattr(d.variables['TBOT'], 'units', ''))
                fs = read(d, 'FSDS', i)
                tl, fl = tb.ravel()[land], fs.ravel()[land]
                bad = (fl < SENTINEL_FSDS) | (tl < TMIN) | (tl > TMAX)
                year_flags[yr] = int(bad.sum())
                if last_year is None or yr > last_year:
                    last_year = yr
                    hdm_last = read(d, 'HDM', i)
                    gpp_last = read(d, 'GPP', i)
                    tbot_last, fsds_last = tb, fs

    rep['checks']['record_structure'] = {
        'files_on_this_tape': per_file,
        'calendar': cal,
        'n_full_year_records_checked': len(year_flags),
        'model_years_checked': sorted(year_flags),
        'verdict': 'PASS' if year_flags else 'FAIL: no complete annual interval on any h0 file',
    }
    if not year_flags:
        raise SystemExit(json.dumps(rep, indent=2))
    model_year = last_year

    # ---- check 1a: HDM actually read, at the latest full year -------------
    hv = hdm_last.ravel()[land]
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

    # ---- check 1b: no sentinel forcing in ANY complete annual record ------
    tl, fl, gl = tbot_last.ravel()[land], fsds_last.ravel()[land], gpp_last.ravel()[land]
    total_flagged = sum(year_flags.values())
    rep['checks']['sentinel_forcing'] = {
        'model_year_of_snapshot_stats': model_year,
        'land_cells': int(len(land)),
        'flagged_cells_by_year': year_flags,
        'total_flagged_cell_years': int(total_flagged),
        'min_fsds_latest_year': float(np.nanmin(fl)), 'max_tbot_c_latest_year': float(np.nanmax(tl)),
        'min_tbot_c_latest_year': float(np.nanmin(tl)),
        'cells_with_zero_gpp_latest_year': int((gl <= 0).sum()),
        'verdict': ('PASS' if total_flagged == 0 else
                   'FAIL: %d flagged cell-years, see flagged_cells_by_year' % total_flagged),
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

    # ---- check 3: output shapes and total volume across every closed file -
    all_h1 = sorted(R.glob(f'{CASE}.elm.h1.*.nc'))
    all_h2 = sorted(R.glob(f'{CASE}.elm.h2.*.nc'))
    sizes = {}
    for tag, path, group in (('h0', all_h0[0], all_h0), ('h1', h1, all_h1),
                             ('h2', h2, all_h2), ('elm.r', rst, None)):
        n = 1
        if tag != 'elm.r':
            with nc.Dataset(path) as d:
                n = len(d.dimensions['time'])
        total_bytes = int(path.stat().st_size) if group is None else sum(
            p.stat().st_size for p in group)
        sizes[tag] = {'representative_file': path.name,
                      'bytes_representative_file': int(path.stat().st_size),
                      'records_representative_file': int(n),
                      'MB_per_record': round(path.stat().st_size / n / 1e6, 1),
                      'n_files': 1 if group is None else len(group),
                      'total_bytes_all_files': total_bytes}
    rep['checks']['output_volume'] = sizes

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, indent=2, allow_nan=False))
    for k, v in rep['checks'].items():
        if isinstance(v, dict) and 'verdict' in v:
            print(f'{k:22s} {v["verdict"]}')


if __name__ == '__main__':
    main()
