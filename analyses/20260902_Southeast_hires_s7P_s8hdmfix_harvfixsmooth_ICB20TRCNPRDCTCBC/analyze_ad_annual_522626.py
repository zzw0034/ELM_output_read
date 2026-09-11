"""Read-only analysis of the annual AD diagnostic, job 522626; run on a compute node.

Job 522626 is `20260910_ADdiag_annual_ICB1850CNRDCTCBC_ad_spinup`: the ORIGINAL
(pre-2026-07-17) HDM executable, so human population density is still zero and
fire is unsuppressed, but the FIRST run to read the repaired zone_mappings.txt.
So its coastal result is a real test of the mapping fix, and its stranded
fractions are control values that must never be quoted as a repaired outcome.

Four deliverables, matching RERUN_VERIFICATION_PLAN.md section 6:
  1. coastal  - do the previously sentinel-driven cells now read physical
                forcing and produce positive GPP, and reconcile the
                194 gridcell / 193 patch / 193 mapping counts
  2. timeline - annual decline of the 405 residual patches, around year 26
  3. resp     - XR = AR - MR - GR, read against CPOOL, XSMRPOOL and temperature
  4. budget   - what the averaged tapes CAN close, what only the single
                restart at year 31 can anchor, and what needs the h3
                instantaneous tape that only the rerun will have

Every tape field here is avgflag='A'. An annual record is the MEAN of the year,
not the state at either end, so no strict per-year leaf carbon closure is
possible from this run. That limit is reported, not worked around.
"""
import argparse
import csv
import json
from pathlib import Path

import netCDF4 as nc
import numpy as np

DIAG_CASE = '20260910_ADdiag_annual_ICB1850CNRDCTCBC_ad_spinup'
REF_CASE = '20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup'
OUTPUT_ROOT = Path('/scratch/hpcl-cli185/zw5/cime_output_dirs')
REF_WINDOW_YEAR = 81           # the h1 file whose 20-year mean defines the residual set
CARBON_ONLY_YEARS = 25         # nyears_ad_carbon_only; N limitation resumes in year 26
FUEL_SWITCH_YEAR = 40          # FireMod.F90 switches the CWD fuel term at kyr >= 40
SENTINEL_FSDS = 1.0            # W/m2; ocean sentinel FSDS is about -1111
SENTINEL_TMIN, SENTINEL_TMAX = -30.0, 45.0   # degrees C
LOW_LAI = 0.5
PINE = 1                       # needleleaf evergreen temperate
NATURAL_LANDUNIT = 1
MIN_WEIGHT = 0.05


def read(d, name, t=None):
    """Read a variable, optionally one time record, as float with NaN fill."""
    v = d.variables[name]
    if v.dimensions and v.dimensions[0] == 'time':
        a = v[0] if t is None else v[t]
    else:
        a = v[:]
    return np.ma.filled(np.asarray(a, dtype=float), np.nan)


def to_celsius(values, units):
    u = (units or '').strip().lower()
    if u in ('k', 'kelvin'):
        return values - 273.15
    if u in ('degc', 'c', 'degrees c', 'celsius', 'degrees_celsius'):
        return values
    raise ValueError('Unknown temperature units: ' + repr(units))


def seconds_per_year(dataset):
    """Refuse to guess the calendar; the flux unit conversion depends on it."""
    cal = (getattr(dataset.variables['time'], 'calendar', '') or '').lower()
    if cal in ('noleap', '365_day'):
        return 365.0 * 86400.0
    raise ValueError('Unexpected calendar %r; set the conversion explicitly' % cal)


def pine_patches(d):
    """Selection identical to diagnose_residual_pine_fire.py, one patch per cell."""
    nlon = len(read(d, 'lon'))
    ix = read(d, 'pfts1d_ixy').astype(int) - 1
    jy = read(d, 'pfts1d_jxy').astype(int) - 1
    wt = read(d, 'pfts1d_wtgcell')
    mask = ((read(d, 'pfts1d_itype_veg') == PINE)
            & (read(d, 'pfts1d_itype_lunit') == NATURAL_LANDUNIT)
            & (wt > MIN_WEIGHT))
    ids = np.flatnonzero(mask)
    key = jy[ids] * nlon + ix[ids]
    if len(np.unique(key)) != len(key):
        raise ValueError('Multiple selected pine patches per cell; refusing to overwrite')
    order = np.argsort(key)
    return ids[order], key[order]


def land_cell_keys(d):
    """Every gridcell that hosts a column, as jy*nlon+ix."""
    nlon = len(read(d, 'lon'))
    ix = read(d, 'cols1d_ixy').astype(int) - 1
    jy = read(d, 'cols1d_jxy').astype(int) - 1
    return np.unique(jy * nlon + ix)


def forcing_flags(h0, t, land):
    """Cells whose annual-mean forcing is a missing-data flag rather than weather."""
    tbot = to_celsius(read(h0, 'TBOT', t), getattr(h0.variables['TBOT'], 'units', ''))
    fsds = read(h0, 'FSDS', t)
    gpp = read(h0, 'GPP', t)
    bad = ((fsds.ravel()[land] < SENTINEL_FSDS)
           | (tbot.ravel()[land] < SENTINEL_TMIN)
           | (tbot.ravel()[land] > SENTINEL_TMAX))
    return bad, tbot.ravel()[land], fsds.ravel()[land], gpp.ravel()[land]


# ---------------------------------------------------------------- 1. coastal

def coastal_audit(diag_run, ref_run, out):
    """Did the repaired mapping remove the sentinel cells, and do 194/193 reconcile?"""
    ref_h1 = ref_run / f'{REF_CASE}.elm.h1.{REF_WINDOW_YEAR:04d}-01-01-00000.nc'
    ref_h0 = Path(str(ref_h1).replace('.h1.', '.h0.'))
    with nc.Dataset(ref_h1) as d, nc.Dataset(ref_h0) as h0:
        land = land_cell_keys(d)
        ids, key = pine_patches(d)
        lai = read(d, 'TLAI')[ids]
        bad, tbot, fsds, _ = forcing_flags(h0, 0, land)
        flagged_cells = land[bad]
        cell_is_flagged = np.isin(key, flagged_cells)
        low = lai < LOW_LAI
        sentinel_patches = low & cell_is_flagged
        residual_patches = low & ~cell_is_flagged
        residual_key = key[residual_patches]
        sentinel_key = key[sentinel_patches]
        nlon = len(read(d, 'lon'))
        lon, lat = read(d, 'lon'), read(d, 'lat')

    recon = {
        'reference_case': REF_CASE,
        'reference_window': f'{REF_WINDOW_YEAR-20}-{REF_WINDOW_YEAR-1}',
        'land_cells': int(len(land)),
        'flagged_land_cells': int(len(flagged_cells)),
        'selected_pine_patches': int(len(key)),
        'low_lai_pine_patches': int(low.sum()),
        'low_lai_on_flagged_cells': int(sentinel_patches.sum()),
        'low_lai_not_on_flagged_cells': int(residual_patches.sum()),
        'flagged_cells_hosting_a_selected_pine_patch':
            int(np.isin(flagged_cells, key).sum()),
        'flagged_cells_without_a_selected_pine_patch':
            int((~np.isin(flagged_cells, key)).sum()),
        'note': ('A flagged cell with no selected pine patch is the expected '
                 'source of a gridcell/patch count mismatch: the patch mask '
                 'requires PFT 1, natural landunit and weight > %.2f.' % MIN_WEIGHT),
    }

    # The same cells, year by year, in the run that read the repaired mapping.
    per_year, still_flagged = [], {}
    diag_h0 = diag_run / f'{DIAG_CASE}.elm.h0.0001-01-01-00000.nc'
    with nc.Dataset(diag_h0) as h0:
        nt = len(h0.dimensions['time'])
        diag_land = land  # same grid; asserted below
        with nc.Dataset(diag_run / f'{DIAG_CASE}.elm.h1.0001-01-01-00000.nc') as d:
            if not np.array_equal(land_cell_keys(d), land):
                raise ValueError('Land cell set differs between the two cases')
        pos = np.searchsorted(diag_land, flagged_cells)
        if not np.array_equal(diag_land[pos], flagged_cells):
            raise ValueError('Flagged cells not found in the diagnostic land mask')
        for t in range(nt):
            bad, tbot, fsds, gpp = forcing_flags(h0, t, diag_land)
            per_year.append({
                'year': t + 1,
                'flagged_land_cells': int(bad.sum()),
                'previously_flagged_still_flagged': int(bad[pos].sum()),
                'previously_flagged_with_positive_gpp': int((gpp[pos] > 0).sum()),
                'previously_flagged_min_gpp': float(np.nanmin(gpp[pos])),
                'previously_flagged_min_fsds': float(np.nanmin(fsds[pos])),
                'previously_flagged_max_tbot': float(np.nanmax(tbot[pos])),
            })
            if t == nt - 1:
                still_flagged = dict(tbot=tbot[pos], fsds=fsds[pos], gpp=gpp[pos])

    with (out / 'coastal_cells.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cell_key', 'lat', 'lon', 'final_year_tbot_c',
                    'final_year_fsds', 'final_year_gpp', 'hosts_selected_pine'])
        for n, cell in enumerate(flagged_cells):
            w.writerow([int(cell), lat[cell // nlon], lon[cell % nlon],
                        still_flagged['tbot'][n], still_flagged['fsds'][n],
                        still_flagged['gpp'][n], bool(np.isin(cell, key))])

    return {'reconciliation': recon, 'per_year': per_year}, residual_key, sentinel_key, key


# --------------------------------------------------- 2, 3. timeline and XR

def patch_timeline(diag_run, groups, out):
    """Annual per-patch trajectories, plus XR by the AR = MR + GR + XR identity."""
    patch_flds = ('TLAI', 'LEAFC', 'GPP', 'NPP', 'LEAFC_ALLOC', 'LEAFC_LOSS',
                  'LEAFC_TO_LITTER', 'CPOOL', 'XSMRPOOL', 'AR', 'MR', 'GR',
                  'BTRAN', 'TOTVEGC', 'LEAFN')
    col_flds = ('FPG', 'FPI', 'FPG_P', 'COL_FIRE_CLOSS', 'SMINN')
    h1 = diag_run / f'{DIAG_CASE}.elm.h1.0001-01-01-00000.nc'
    h0 = diag_run / f'{DIAG_CASE}.elm.h0.0001-01-01-00000.nc'
    series = {}
    with nc.Dataset(h1) as d, nc.Dataset(h0) as g:
        spy = seconds_per_year(d)
        nlon = len(read(d, 'lon'))
        nt = len(d.dimensions['time'])
        ids, key = pine_patches(d)
        col_ix = read(d, 'cols1d_ixy').astype(int) - 1
        col_jy = read(d, 'cols1d_jxy').astype(int) - 1
        col_key = col_jy * nlon + col_ix
        col_wt = read(d, 'cols1d_wtgcell')
        col_nat = read(d, 'cols1d_itype_lunit') == NATURAL_LANDUNIT
        size = len(read(d, 'lat')) * nlon
        index = {name: np.flatnonzero(np.isin(key, k)) for name, k in groups.items()}
        take = np.unique(np.concatenate(list(index.values())))
        rows = ids[take]
        tbot_units = getattr(g.variables['TBOT'], 'units', '')
        for t in range(nt):
            rec = {'year': t + 1}
            for name in patch_flds:
                rec[name] = read(d, name, t)[rows]
            cell = key[take]
            rec['TBOT'] = to_celsius(read(g, 'TBOT', t), tbot_units).ravel()[cell]
            rec['FSDS'] = read(g, 'FSDS', t).ravel()[cell]
            for name in col_flds:
                val = read(d, name, t)
                ok = np.isfinite(val) & (col_wt > 0) & col_nat
                den = np.bincount(col_key[ok], weights=col_wt[ok], minlength=size)
                num = np.bincount(col_key[ok], weights=col_wt[ok] * val[ok], minlength=size)
                grid = np.divide(num, den, out=np.full(size, np.nan), where=den > 0)
                rec[name] = grid[cell]
            # AR = MR + GR + XR for the non-crop nu_com='RD' branch
            # (VegetationDataType.F90:8256). XR is not on this tape; recover it.
            rec['XR'] = rec['AR'] - rec['MR'] - rec['GR']
            rec['fire_gC_m2_yr'] = rec['COL_FIRE_CLOSS'] * spy
            series[t + 1] = rec
        lat, lon = read(d, 'lat'), read(d, 'lon')
        meta = {'key': key[take], 'lat': lat[key[take] // nlon],
                'lon': lon[key[take] % nlon], 'seconds_per_year': spy,
                'nlon': nlon}
    local = {name: np.searchsorted(take, index[name]) for name in index}
    return series, meta, local, take


def first_crossing(series, rows, field, threshold, below=True):
    """First year each patch crosses a threshold; NaN if it never does."""
    years = sorted(series)
    out = np.full(len(rows), np.nan)
    for y in years:
        v = series[y][field][rows]
        hit = (v < threshold) if below else (v > threshold)
        new = np.isnan(out) & hit
        out[new] = y
    return out


def stats(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if not len(a):
        return {'n': 0}
    return {'n': int(len(a)), 'mean': float(a.mean()), 'median': float(np.median(a)),
            'p25': float(np.quantile(a, .25)), 'p75': float(np.quantile(a, .75))}


# ------------------------------------------------------------- 4. budget

def budget_inventory(series, meta, rows, restart, out):
    """What the averaged tapes can close, what the restart anchors, what neither can."""
    spy = meta['seconds_per_year']
    years = sorted(series)
    approx = []
    for a, b in zip(years, years[1:]):
        # NOTE: a difference of annual MEANS is not the year's change in state.
        # This is an approximate consistency check, deliberately labelled as one.
        d_mean = series[b]['LEAFC'][rows] - series[a]['LEAFC'][rows]
        net_flux = (series[a]['LEAFC_ALLOC'][rows] - series[a]['LEAFC_LOSS'][rows]) * spy
        lumped = (series[a]['LEAFC_LOSS'][rows] - series[a]['LEAFC_TO_LITTER'][rows]) * spy
        approx.append({
            'from_year': a, 'to_year': b,
            'delta_annual_mean_leafc': stats(d_mean),
            'net_flux_gC_m2_yr': stats(net_flux),
            'difference': stats(d_mean - net_flux),
            'non_litterfall_loss_gC_m2_yr': stats(lumped),
        })

    anchor = {'available': restart is not None}
    if restart is not None:
        exact, last = restart['leafc'], series[years[-1]]['LEAFC'][rows]
        anchor.update({
            'restart_file': restart['path'],
            'restart_leafc_at_year_boundary': stats(exact),
            'final_year_annual_mean_leafc': stats(last),
            'mean_minus_state': stats(last - exact),
            'note': ('Quantifies the error made by substituting an annual mean '
                     'for an end-of-year state. It is one anchor, at one date, '
                     'and cannot close any individual year.'),
        })

    return {
        'approximate_consistency_by_year': approx,
        'exact_anchor_year_31': anchor,
        'closable_now': [
            'Approximate consistency of LEAFC_ALLOC - LEAFC_LOSS against the '
            'year-to-year change in annual-mean LEAFC, labelled approximate.',
            'LEAFC_LOSS - LEAFC_TO_LITTER as one lumped non-litterfall loss term.',
            'XR = AR - MR - GR per patch per year, with CPOOL, XSMRPOOL and TBOT.',
            'Annual timing of TLAI and LEAFC decline, free of the 20-year smear.',
        ],
        'anchored_once_only': [
            'Exact leaf carbon state at the year-31 boundary, from elm.r, which '
            'measures how far an annual mean sits from the end-of-year state.',
        ],
        'needs_the_h3_instantaneous_tape': [
            'Strict per-year closure: LEAFC(end) - LEAFC(previous end) against '
            'the integrated fluxes of that year.',
            'The size of the PrecisionControlMod truncation term, which removes '
            'leaf carbon without any flux recording it and is most active in '
            'exactly the collapsing patches.',
            'Separation of a patch-weight transfer from a truncation residual.',
        ],
        'not_answerable_by_this_run_at_all': [
            'Any split of fire from background mortality: M_LEAFC_TO_FIRE, '
            'M_LEAFC_TO_LITTER_FIRE and M_LEAFC_TO_LITTER are default=inactive '
            'and absent from this case hist_fincl.',
            'Any combined-fix vegetation outcome: this run uses the pre-fix HDM '
            'executable, so its stranded fractions are control values.',
        ],
    }


def read_restart(diag_run, cell_keys, nlon):
    """Exact leaf carbon at the year-31 boundary, joined by identity not by order."""
    path = diag_run / f'{DIAG_CASE}.elm.r.0031-01-01-00000.nc'
    if not path.exists():
        return None
    with nc.Dataset(path) as r:
        ix = read(r, 'pfts1d_ixy').astype(int) - 1
        jy = read(r, 'pfts1d_jxy').astype(int) - 1
        mask = ((read(r, 'pfts1d_itypveg') == PINE)
                & (read(r, 'pfts1d_ityplun') == NATURAL_LANDUNIT)
                & (read(r, 'pfts1d_wtxy') > MIN_WEIGHT))
        ids = np.flatnonzero(mask)
        key = jy[ids] * nlon + ix[ids]
        if len(np.unique(key)) != len(key):
            raise ValueError('Multiple restart pine patches per cell; refusing to join')
        order = np.argsort(key)
        ids, key = ids[order], key[order]
        pos = np.searchsorted(key, cell_keys)
        if not (pos < len(key)).all() or not np.array_equal(key[pos], cell_keys):
            raise ValueError('Restart patch identities do not cover the tracked cells')
        return {'path': str(path), 'leafc': read(r, 'leafc')[ids[pos]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diag-run', type=Path, default=OUTPUT_ROOT / DIAG_CASE / 'run')
    parser.add_argument('--ref-run', type=Path, default=OUTPUT_ROOT / REF_CASE / 'run')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--skip-restart', action='store_true',
                        help='skip the 14.85 GB restart read')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    coastal, residual_key, sentinel_key, pine_key = coastal_audit(
        args.diag_run, args.ref_run, args.output_dir)

    healthy_key = np.setdiff1d(pine_key, np.concatenate([residual_key, sentinel_key]))
    rng = np.random.default_rng(0)
    healthy_key = np.sort(rng.choice(healthy_key, size=min(2000, len(healthy_key)),
                                     replace=False))
    groups = {'residual': residual_key, 'sentinel': sentinel_key,
              'healthy_sample': healthy_key}
    series, meta, local, take = patch_timeline(args.diag_run, groups, args.output_dir)

    report = {'case': DIAG_CASE, 'coastal': coastal, 'groups': {}, 'timing': {},
              'caveats': [
                  'Pre-fix HDM executable: stranded fractions here are CONTROL values.',
                  'Repaired zone_mappings.txt: the coastal result IS a real test.',
                  'Every field is avgflag=A, so no strict per-year state budget exists.',
                  'XR is recovered from AR - MR - GR, not read from its own field.',
                  'A healthy sample of up to 2000 patches is a sample, not a census.',
              ]}

    fields = ('TLAI', 'LEAFC', 'GPP', 'NPP', 'LEAFC_ALLOC', 'LEAFC_LOSS',
              'LEAFC_TO_LITTER', 'XR', 'AR', 'MR', 'GR', 'CPOOL', 'XSMRPOOL',
              'BTRAN', 'FPG', 'FPI', 'fire_gC_m2_yr', 'TBOT', 'FSDS')
    for name, rows in local.items():
        report['groups'][name] = {
            'n': int(len(rows)),
            'by_year': {str(y): {f: stats(series[y][f][rows]) for f in fields}
                        for y in sorted(series)},
        }
        lai_cross = first_crossing(series, rows, 'TLAI', LOW_LAI)
        zero_leaf = first_crossing(series, rows, 'LEAFC', 1e-6)
        report['timing'][name] = {
            'first_year_tlai_below_%.1f' % LOW_LAI: stats(lai_cross),
            'never_crossed': int(np.isnan(lai_cross).sum()),
            'first_year_leafc_below_1e-6': stats(zero_leaf),
            'crossed_before_year_%d' % (CARBON_ONLY_YEARS + 1):
                int(np.nansum(lai_cross <= CARBON_ONLY_YEARS)),
            'crossed_after_carbon_only_ends':
                int(np.nansum(lai_cross > CARBON_ONLY_YEARS)),
            'crossed_after_fuel_switch_year_%d' % FUEL_SWITCH_YEAR:
                int(np.nansum(lai_cross > FUEL_SWITCH_YEAR)),
        }

    rows = local['residual']
    restart = None
    if not args.skip_restart:
        restart = read_restart(args.diag_run, meta['key'][rows], meta['nlon'])
    report['budget'] = budget_inventory(series, meta, rows, restart, args.output_dir)

    with (args.output_dir / 'summary.json').open('w') as f:
        json.dump(report, f, indent=2, allow_nan=False)
    with (args.output_dir / 'annual_trajectory.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['group', 'cell_key', 'lat', 'lon', 'year', *fields])
        for name, rows in local.items():
            for n, r in enumerate(rows):
                for y in sorted(series):
                    w.writerow([name, int(meta['key'][r]), meta['lat'][r],
                                meta['lon'][r], y,
                                *[series[y][fld][r] for fld in fields]])
    print(json.dumps(coastal['reconciliation'], indent=2))
    print(json.dumps(coastal['per_year'][-1], indent=2))


if __name__ == '__main__':
    main()
