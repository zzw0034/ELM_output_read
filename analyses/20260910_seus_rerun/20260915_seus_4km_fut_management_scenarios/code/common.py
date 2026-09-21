"""Shared helpers for the 20260915 4km SEUS management-scenario batch: DF
(deforestation counterfactual) and RH (reduced harvest) for SSP1-1.9,
SSP2-4.5, SSP5-8.5 (2024-2100). These are the 6 cases whose landuse input
had the PCT_NAT_PFT float32-precision bug (see
ELM_Futu_landuseInput/future_runs/docs/BLOCKER_pct_nat_pft_sum.md), rebuilt
and rerun 2026-09-20/21 -- this folder is the post-fix sanity check.

Import from other scripts in this folder -- do not run directly. All scripts
using this module must run via Slurm (sbatch), never on the Pathfinder login
node -- the 4km grid's h0 files are ~12 GB apiece.
"""
import glob
import os
import re
import warnings

import numpy as np
import xarray as xr

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
OUTDIR_ROOT = ("/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/"
               "20260915_seus_4km_fut_management_scenarios/figure")

SEC_PER_YEAR_NOLEAP = 365 * 86400.0

CASES = {
    "SSP1-1.9 DF": "20260915_seus_4km_fut_ssp119_DF",
    "SSP1-1.9 RH": "20260915_seus_4km_fut_ssp119_RH",
    "SSP2-4.5 DF": "20260915_seus_4km_fut_ssp245_DF",
    "SSP2-4.5 RH": "20260915_seus_4km_fut_ssp245_RH",
    "SSP5-8.5 DF": "20260915_seus_4km_fut_ssp585_DF",
    "SSP5-8.5 RH": "20260915_seus_4km_fut_ssp585_RH",
}


def h0_files(case):
    d = os.path.join(CASE_ROOT, case, "run")
    return sorted(glob.glob(os.path.join(d, f"{case}.elm.h0.*.nc")))


def year_of(fname):
    m = re.search(r"\.h0\.(\d+)-", fname)
    return int(m.group(1))


def h0_file_for_year(case, year):
    matches = [f for f in h0_files(case) if year_of(f) == year]
    if not matches:
        raise ValueError(f"No h0 file found for year {year} in {case}")
    return matches[0]


def day_weighted_annual_mean(da, time_bounds):
    """Day-length-weighted mean over the time dimension of a monthly h0
    variable. See elm_monthly_output_weight_by_month_length memory -- do not
    replace this with a plain .mean(axis=0) or .isel(time=0)."""
    vals = da.values
    if vals.shape[0] == 1:
        return vals[0]
    if time_bounds is None:
        warnings.warn("day_weighted_annual_mean: no time_bounds, falling back "
                       "to an unweighted mean over the time dimension", RuntimeWarning)
        return np.nanmean(vals, axis=0)
    dt = time_bounds[:, 1] - time_bounds[:, 0]
    dt = dt.astype(float)
    w = dt / dt.sum()
    shape = (len(w),) + (1,) * (vals.ndim - 1)
    w_full = np.broadcast_to(w.reshape(shape), vals.shape)
    finite = np.isfinite(vals)
    w_masked = np.where(finite, w_full, 0.0)
    w_sum = w_masked.sum(axis=0)
    out = np.full(vals.shape[1:], np.nan)
    valid = w_sum > 0
    out[valid] = np.nansum(np.where(finite, vals, 0.0) * w_masked, axis=0)[valid] / w_sum[valid]
    return out


def load_mean_map(case, var, year_min, year_max):
    """Mean of the day-weighted annual mean over [year_min, year_max]."""
    files = [f for f in h0_files(case) if year_min <= year_of(f) <= year_max]
    if not files:
        raise ValueError(f"No h0 files for {case} in [{year_min},{year_max}]")
    stack = []
    lat = lon = None
    units = None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        vals = day_weighted_annual_mean(ds[var], tb)
        units = ds[var].attrs.get("units", "")
        if units.strip() == "gC/m^2/s":
            vals = vals * SEC_PER_YEAR_NOLEAP
        stack.append(vals)
        if lat is None:
            lat = ds["lat"].values
            lon = ds["lon"].values
        ds.close()
    mean_map = np.nanmean(np.stack(stack, axis=0), axis=0)
    return lon, lat, mean_map
