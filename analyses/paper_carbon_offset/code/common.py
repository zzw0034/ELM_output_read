"""
Shared helpers for the SEUS manuscript figures at both resolutions.

The agreed argument is in MANUSCRIPT_BLUEPRINT.md; the cohort decision and the
case list are in CASE_MATRIX.md (decided 2026-09-23). Existing fig01-fig06
numbers are asset IDs, not the new manuscript figure numbers.

Case names live ONLY in COHORTS below. The active cohort is PAPER_COHORT
(default "rerun_20260910"); override without editing code via
    sbatch --export=NONE,PAPER_COHORT=legacy_20260908 ... code/submit_py.sbatch code/<script.py> ...
Caches and figures go to per-cohort subfolders, because the caches carry no
source-version signature and must never be reused across cohorts. A later
crit_dayl_stress=38000 s cohort is added as one more COHORTS entry.
"""
import glob
import os
import re
import warnings

import numpy as np
import xarray as xr

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs"
BASE = "/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset"

SEC_PER_YEAR_NOLEAP = 365 * 86400.0

# ---------------------------------------------------------------- case names

SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
MANAGEMENT = ["RF", "DF", "RH"]
_SSP_TAG = {"SSP1-1.9": "ssp119", "SSP2-4.5": "ssp245", "SSP3-7.0": "ssp370", "SSP5-8.5": "ssp585"}


def _rerun_halfdeg():
    # 20260911 created the four Default SSPs and the SSP3-7.0 management
    # cases; 20260915 added management for the other three SSPs.
    cases = {"transient": "20260911_seus_halfdeg_transient_dt3600"}
    for ssp, tag in _SSP_TAG.items():
        cases[ssp] = f"20260911_seus_halfdeg_future_{tag}_dt3600"
        date = "20260911" if tag == "ssp370" else "20260915"
        for m in MANAGEMENT:
            cases[f"{ssp} {m}"] = f"{date}_seus_halfdeg_future_{tag}_{m}_dt3600"
    return cases


def _rerun_fourkm():
    # 20260917 holds the four Defaults and SSP3-7.0 management; 20260915 the
    # other SSPs' management. All share the 4 km transient's executable.
    cases = {"transient": "20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC"}
    for ssp, tag in _SSP_TAG.items():
        cases[ssp] = f"20260917_seus_4km_fut_{tag}"
        date = "20260917" if tag == "ssp370" else "20260915"
        for m in MANAGEMENT:
            cases[f"{ssp} {m}"] = f"{date}_seus_4km_fut_{tag}_{m}"
    return cases


# Each cohort: resolution -> (case dict, subdir under CASE_ROOT).
COHORTS = {
    # Manuscript cohort (CASE_MATRIX.md): 4 SSPs x Default/RF/DF/RH at both
    # resolutions, crit_dayl_stress = 36000 s, analysed as if 38000 s.
    "rerun_20260910": {
        "0.5deg": (_rerun_halfdeg(), "20260910_seus_rerun"),
        "4km": (_rerun_fourkm(), "20260910_seus_rerun"),
    },
    # Legacy figure cohort (void for the paper). Its 4 km futures were
    # archived to /projects/.../e3sm_run/20260901_before_seus_rerun, so these
    # scratch paths may no longer resolve.
    "legacy_20260908": {
        "0.5deg": ({
            "transient": "20260911_seus_halfdeg_transient_dt3600",
            "SSP1-1.9": "20260911_seus_halfdeg_future_ssp119_dt3600",
            "SSP2-4.5": "20260911_seus_halfdeg_future_ssp245_dt3600",
            "SSP3-7.0": "20260911_seus_halfdeg_future_ssp370_dt3600",
            "SSP3-7.0 RF": "20260911_seus_halfdeg_future_ssp370_RF_dt3600",
            "SSP3-7.0 DF": "20260911_seus_halfdeg_future_ssp370_DF_dt3600",
            "SSP3-7.0 RH": "20260911_seus_halfdeg_future_ssp370_RH_dt3600",
            "SSP5-8.5": "20260911_seus_halfdeg_future_ssp585_dt3600",
        }, "20260910_seus_rerun"),
        "4km": ({
            "transient": "20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC",
            "SSP1-1.9": "20260908_seus_4km_fut_ssp119",
            "SSP2-4.5": "20260908_seus_4km_fut_ssp245",
            "SSP3-7.0": "20260908_seus_4km_fut_ssp370",
            "SSP3-7.0 RF": "20260908_seus_4km_fut_ssp370_RF",
            "SSP3-7.0 DF": "20260908_seus_4km_fut_ssp370_DF",
            "SSP3-7.0 RH": "20260908_seus_4km_fut_ssp370_RH",
            "SSP5-8.5": "20260908_seus_4km_fut_ssp585",
        }, ""),
    },
}

PAPER_COHORT = os.environ.get("PAPER_COHORT", "rerun_20260910")
if PAPER_COHORT not in COHORTS:
    raise KeyError(f"PAPER_COHORT={PAPER_COHORT!r} not in {sorted(COHORTS)}")

# Legacy PNGs are preserved in figures/legacy; new cohorts write separately.
OUTDIR = os.path.join(BASE, "figures", PAPER_COHORT)
CACHE_DIR = os.path.join(BASE, "_cache", PAPER_COHORT)

RESOLUTIONS = COHORTS[PAPER_COHORT]
HALFDEG, HALFDEG_SUBDIR = RESOLUTIONS["0.5deg"]
FOURKM, FOURKM_SUBDIR = RESOLUTIONS["4km"]

# Proposal Table 2. Sign convention is the proposal's: each entry is
# (positive_term, negative_term) so that offset = positive - negative comes
# out >0 when the management stores carbon. Note DF is reversed relative to
# RF/RH -- that is intentional and comes straight from the proposal.
def offset_defs(ssp="SSP3-7.0"):
    """(positive, negative) case keys for the three management benefits in one SSP."""
    return {
        "Restoration/protection\n(RF - Default)": (f"{ssp} RF", ssp),
        "Avoided-loss upper bound\n(Default - DF)": (ssp, f"{ssp} DF"),
        "Reduced harvest\n(RH - Default)": (f"{ssp} RH", ssp),
    }


# Legacy figure scripts use the SSP3-7.0 definitions directly.
OFFSET_DEFS = offset_defs("SSP3-7.0")
OFFSET_COLORS = {
    "Restoration/protection\n(RF - Default)": "tab:blue",
    "Avoided-loss upper bound\n(Default - DF)": "tab:red",
    "Reduced harvest\n(RH - Default)": "tab:purple",
}

# Carbon pool components for the partitioning figure. TOTECOSYSC is a native
# h0 variable -- use it directly rather than summing, and cross-check.
POOL_COMPONENTS = [
    ("LEAFC", "Leaf"),
    ("LIVESTEMC", "Live stem (aboveground wood)"),
    ("DEADSTEMC", "Dead stem (aboveground wood)"),
    ("FROOTC", "Fine root"),
    ("LIVECROOTC", "Live coarse root"),
    ("DEADCROOTC", "Dead coarse root"),
    ("CWDC", "Coarse woody debris"),
    ("TOTLITC", "Litter"),
    ("TOTSOMC", "Soil organic carbon"),
]


def case_dir(case, subdir):
    return os.path.join(CASE_ROOT, subdir, case, "run") if subdir else os.path.join(CASE_ROOT, case, "run")


def h0_files(case, subdir=""):
    d = case_dir(case, subdir)
    return sorted(glob.glob(os.path.join(d, f"{case}.elm.h0.*.nc")))


def h1_files(case, subdir=""):
    d = case_dir(case, subdir)
    return sorted(glob.glob(os.path.join(d, f"{case}.elm.h1.*.nc")))


def year_of(fname):
    m = re.search(r"\.h[01]\.(\d+)-", fname)
    return int(m.group(1))


def day_weighted_annual_mean(da, time_bounds):
    """Day-length-weighted mean over the time dimension.

    Handles both single-record files and the 12-record monthly files used by
    the transient/future cases. NEVER replace this with `.isel(time=0)` or a
    bare `.mean(axis=0)`: monthly records have unequal lengths under noleap,
    and an earlier version of this pipeline that took only January inflated
    NBP by ~15x. Also note the spinup cases bundle many *annual* records per
    file (hist_nhtfrq=-8760), so `time` size alone does not tell you the
    averaging period -- check the case's own lnd_in.

    Fixed 2026-09-15 (Codex review) -- two silent-failure modes:
      1. Falling back to an unweighted `nanmean` when time_bounds is missing
         used to happen with no signal at all. Now it warns.
      2. `nansum(vals*w)` treats an entirely-NaN time series as a weighted
         sum of zeros (-> 0.0, not NaN), and does not renormalize weights
         when only *some* months are missing (silently underweights that
         year instead of averaging over the months actually present). Now:
         gridcells/columns with all-NaN input return NaN, and partial
         missingness renormalizes the weights over the finite months only.
    """
    vals = da.values
    if vals.shape[0] == 1:
        return vals[0]
    if time_bounds is None:
        warnings.warn("day_weighted_annual_mean: no time_bounds, falling back "
                       "to an unweighted mean over the time dimension", RuntimeWarning)
        return np.nanmean(vals, axis=0)
    dt = (time_bounds[:, 1] - time_bounds[:, 0]).astype(float)
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


def area_weights(ds):
    """Land area per gridcell in km^2 (area * landfrac)."""
    area = ds["area"].values
    landfrac = ds["landfrac"].values
    w = area * landfrac
    return np.where(np.isfinite(w), w, 0.0)


def domain_total_PgC(values_per_m2, weights_km2):
    """Domain total in PgC from a gC/m2 field. 1 km^2 = 1e6 m2, 1 Pg = 1e15 g."""
    v = np.where(np.isfinite(values_per_m2), values_per_m2, np.nan)
    mask = np.isfinite(v) & (weights_km2 > 0)
    if mask.sum() == 0:
        return np.nan
    return float(np.nansum(v[mask] * weights_km2[mask] * 1e6) / 1e15)


def domain_mean(values, weights):
    v = np.where(np.isfinite(values), values, np.nan)
    mask = np.isfinite(v) & (weights > 0)
    if mask.sum() == 0:
        return np.nan
    return float(np.nansum(v[mask] * weights[mask]) / np.nansum(weights[mask]))


def load_annual_series(case, varnames, subdir="", year_min=None, year_max=None):
    """Annual domain-mean (gC/m2 or gC/m2/yr) and domain-total (PgC) series.

    Opening a 4 km h0 file is expensive (7.5-12 GB), so pass year_min/year_max
    whenever only part of a case is needed.
    """
    files = h0_files(case, subdir)
    if year_min is not None:
        files = [f for f in files if year_of(f) >= year_min]
    if year_max is not None:
        files = [f for f in files if year_of(f) <= year_max]

    out = {"year": []}
    for v in varnames:
        out[v] = []
        out[v + "_PgC"] = []

    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        w = area_weights(ds)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        out["year"].append(year_of(f))
        for v in varnames:
            vals = day_weighted_annual_mean(ds[v], tb)
            if ds[v].attrs.get("units", "").strip() == "gC/m^2/s":
                vals = vals * SEC_PER_YEAR_NOLEAP
            out[v].append(domain_mean(vals, w))
            out[v + "_PgC"].append(domain_total_PgC(vals, w))
        ds.close()

    return {k: np.array(v) for k, v in out.items()}


def load_mean_map(case, var, year_min, year_max, subdir=""):
    """Multi-year mean map of one variable. Returns (lon, lat, 2-D field)."""
    files = [f for f in h0_files(case, subdir) if year_min <= year_of(f) <= year_max]
    if not files:
        raise ValueError(f"no h0 files for {case} in [{year_min},{year_max}]")
    stack, lat, lon = [], None, None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        vals = day_weighted_annual_mean(ds[var], tb)
        if ds[var].attrs.get("units", "").strip() == "gC/m^2/s":
            vals = vals * SEC_PER_YEAR_NOLEAP
        stack.append(vals)
        if lat is None:
            lat, lon = ds["lat"].values, ds["lon"].values
        ds.close()
    return lon, lat, np.nanmean(np.stack(stack, axis=0), axis=0)


def save_cache(series, key):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{key}.npz")
    np.savez(path, **series)
    return path


def load_cache(key):
    npz = np.load(os.path.join(CACHE_DIR, f"{key}.npz"))
    return {k: npz[k] for k in npz.files}


def cache_exists(key):
    return os.path.exists(os.path.join(CACHE_DIR, f"{key}.npz"))
