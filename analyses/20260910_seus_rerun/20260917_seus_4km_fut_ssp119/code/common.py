"""Shared helpers for the 4km SEUS SSP1-1.9 future run
20260917_seus_4km_fut_ssp119 (2024-2100), the 18-node-PE-layout rerun living
under .../cime_output_dirs/20260910_seus_rerun/ (distinct from the older,
pre-rerun 20260908_seus_4km_fut_* case family in ../../20260908_seus_4km/).

Import from other scripts in this folder -- do not run directly. All scripts
using this module must run via Slurm (sbatch), never on the Pathfinder login
node -- the 4km grid's h0 files are ~12 GB apiece (324x504 grid, monthly,
2024-2100), well past what the project's CLAUDE.md/AGENTS.md allow on a
login node.
"""
import glob
import os
import re
import warnings

import numpy as np
import xarray as xr

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
CASE = "20260917_seus_4km_fut_ssp119"
OUTDIR_ROOT = ("/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/"
               "20260917_seus_4km_fut_ssp119/figure")

SEC_PER_YEAR_NOLEAP = 365 * 86400.0

# Variables confirmed present in this case's h0 output (2026-09-18 ncdump -h
# check), with the unit handling each needs before annual-mean plotting:
#   - GPP, NPP, PFT_FIRE_CLOSS: gC/m^2/s -> multiply by SEC_PER_YEAR_NOLEAP
#     for a gC/m^2/yr annual total.
#   - TOTSOMC_1m: gC/m^2, a state variable -- no rate conversion.
#   - FAREA_BURNED: "timestep fractional area burned", units attribute is
#     just "proportion" but (per CLM/ELM fire-code convention) it is a
#     per-second instantaneous rate like the gC/m^2/s fluxes, not an
#     already-annualized fraction. Multiply by SEC_PER_YEAR_NOLEAP the same
#     way to get an annual burned-area fraction; without this the raw
#     monthly-mean values are ~1e-8-1e-6 and unplottable. Flagged here
#     because it is a common misread of this variable -- verify against a
#     domain-total sanity check (annual burned fraction should be a few
#     tenths of a percent to a few percent for the SE US) before trusting it
#     for anything beyond a relative spatial pattern.
VAR_SPECS = [
    ("GPP", "gC m$^{-2}$ yr$^{-1}$", "viridis", "flux"),
    ("NPP", "gC m$^{-2}$ yr$^{-1}$", "viridis", "flux"),
    ("TOTSOMC_1m", "gC m$^{-2}$", "copper_r", "state"),
    ("FAREA_BURNED", "proportion yr$^{-1}$", "Oranges", "rate_annualize"),
    ("PFT_FIRE_CLOSS", "gC m$^{-2}$ yr$^{-1}$", "Reds", "flux"),
]

SNAPSHOT_YEARS = [2024, 2044, 2064, 2084, 2100]


def h0_files():
    d = os.path.join(CASE_ROOT, CASE, "run")
    return sorted(glob.glob(os.path.join(d, f"{CASE}.elm.h0.*.nc")))


def year_of(fname):
    m = re.search(r"\.h0\.(\d+)-", fname)
    return int(m.group(1))


def h0_file_for_year(year):
    matches = [f for f in h0_files() if year_of(f) == year]
    if not matches:
        raise ValueError(f"No h0 file found for year {year} in {CASE}")
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


def load_year_map(var, year, kind):
    """Day-weighted annual-mean spatial map of `var` for a single calendar
    year, from that year's own h0 file. `kind` picks the unit conversion
    (see VAR_SPECS docstring above)."""
    f = h0_file_for_year(year)
    ds = xr.open_dataset(f, decode_times=False)
    tb = ds["time_bounds"].values if "time_bounds" in ds else None
    vals = day_weighted_annual_mean(ds[var], tb)
    if kind in ("flux", "rate_annualize"):
        vals = vals * SEC_PER_YEAR_NOLEAP
    lat = ds["lat"].values
    lon = ds["lon"].values
    ds.close()
    return lon, lat, vals
