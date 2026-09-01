"""
QC check for the 0.5 deg SEUS transient run (20260901_seus_halfdeg_transient):
domain-mean annual time series of GPP, biomass (TOTVEGC / TOTVEGC_ABG /
belowground = TOTVEGC-TOTVEGC_ABG), and soil organic C (0-30 cm, computed
here, and the model's native 0-100 cm TOTSOMC_1m for reference).
NDEP_TO_SMINN is also carried through, since the Ndep stream_year_last_ndep
fix on this same case (2026-09-01) is what this run is meant to validate.

Also carries a broader diagnostic set flagged after the first look at this
run's TOTVEGC vs TOTVEGC_ABG divergence:
  - energy/water balance: EFLX_LH_TOT, FSH, QRUNOFF, RAIN, SNOW
  - fire/disturbance: PFT_FIRE_CLOSS, FAREA_BURNED (this output has no
    COL_FIRE_CLOSS)
  - N limitation: SMINN, SUPPLEMENT_TO_SMINN (should stay near 0 -- large
    sustained values would mean the model is leaning on non-mechanistic N
    supply rather than the real N cycle to sustain productivity)
  - harvest: WOOD_HARVESTC, WOOD_HARVESTN (this output has no
    HRV_XSMRPOOL_TO_ATM)

Unlike the 4 km hires cases elmtools/scatter_to_grid was written for, this
0.5 deg run's h0 output is already on a regular (time, lat, lon) grid, so no
unstructured-column scatter step is needed.

Domain means are area*landfrac-weighted (never a bare lat/lon mean over a
grid that includes ocean cells -- see the project's weighted-vs-unweighted
QA note) and computed here on the native grid, before the file is pulled
back to the Mac, since the output (one value per year) is tiny.

Runs on Pathfinder (Slurm; see run_extract_annual_timeseries.slurm).

Usage: python extract_annual_timeseries.py
"""

import os
import sys

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import (
    aggregate_monthly_to_yearly,
    flux_to_monthly,
    integrate_soil_profile_to_depth,
)

# ── Paths ─────────────────────────────────────────────────────────────────
CASE = "20260901_seus_halfdeg_transient"
RUN_DIR = f"/scratch/hpcl-cli185/zw5/cime_output_dirs/{CASE}/run"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

POOL_VARS = ["TOTVEGC", "TOTVEGC_ABG", "TOTSOMC_1m", "SMINN"]
FLUX_VARS = [
    "GPP", "NPP",
    "WOOD_HARVESTC", "WOOD_HARVESTN",  # gC,gN/m^2/s -- wood harvest to product pools
    "PFT_FIRE_CLOSS",                   # gC/m^2/s -- fire C loss (no COL_FIRE_CLOSS in this output)
    "FAREA_BURNED",                     # 1/s burned-area rate -- summed to an annual burned-fraction approximation
    "RAIN", "SNOW", "QRUNOFF",          # mm/s -> mm/yr
]
# Energy fluxes: annual *mean* rate (W/m^2), not a time-integrated total.
MEAN_RATE_VARS = ["EFLX_LH_TOT", "FSH"]
VR_SOC_VARS = ["SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]
OTHER_VARS = ["NDEP_TO_SMINN", "SUPPLEMENT_TO_SMINN"]  # flux, gN/m^2/s
COORD_VARS = ["area", "landfrac", "levdcmp"]

SOC_DEPTH_M = 0.3


def load_all_vars(files: list[str], varnames: list[str]) -> xr.Dataset:
    """Open each year's h0 file, keep only *varnames* (+ coords), concat
    along time. Mirrors extract_biomass_soc.py's approach for this case's
    conda env (no dask).

    Skips any file with a single time record: the run's very first h0 file
    (1850-01-01) is a one-off instantaneous dump of time-invariant soil
    properties at case start (time=1), not one of the 12-month annual
    bundles the rest of the series is made of, and lacks most prognostic
    variables (e.g. TOTVEGC_ABG)."""
    per_var = {v: [] for v in varnames}
    static = {}
    got_static = False
    for f in files:
        with xr.open_dataset(f, decode_times=True) as ds:
            if ds.sizes.get("time", 0) < 12:
                print(f"  skipping {os.path.basename(f)} (time size {ds.sizes.get('time')}, not a monthly bundle)")
                continue
            for v in varnames:
                per_var[v].append(ds[v].load())
            if not got_static:
                for c in COORD_VARS:
                    static[c] = ds[c].load()
                got_static = True
    out = xr.Dataset({v: xr.concat(das, dim="time") for v, das in per_var.items()})
    for c, da in static.items():
        out[c] = da
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    files = find_h0_files(RUN_DIR)
    print(f"Found {len(files)} h0 files: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}")

    all_vars = POOL_VARS + FLUX_VARS + MEAN_RATE_VARS + VR_SOC_VARS + OTHER_VARS
    ds = load_all_vars(files, all_vars)

    weight = (ds["area"] * ds["landfrac"]).fillna(0.0)

    def weighted_annual(da_yearly: xr.DataArray) -> xr.DataArray:
        return da_yearly.weighted(weight).mean(dim=["lat", "lon"], skipna=True)

    result = {}

    # Pools: monthly -> per-calendar-year mean (with the h0 1-month stamp fix
    # built into aggregate_monthly_to_yearly) -> weighted domain mean.
    for v in POOL_VARS:
        yearly = aggregate_monthly_to_yearly(ds[v], method="mean")
        result[v] = weighted_annual(yearly)

    # Fluxes: gC, gN, or mm /s -> monthly totals -> annual totals (sum) ->
    # weighted domain mean, still expressed per unit area per year.
    for v in FLUX_VARS + OTHER_VARS:
        monthly_total = flux_to_monthly(ds[v])
        yearly = aggregate_monthly_to_yearly(monthly_total, method="sum")
        result[v] = weighted_annual(yearly)

    # Energy fluxes (W/m^2): annual mean rate, not a time-integrated total.
    for v in MEAN_RATE_VARS:
        yearly = aggregate_monthly_to_yearly(ds[v], method="mean")
        result[v] = weighted_annual(yearly)

    # 0-30 cm SOC: sum the 4 soil pools' vertically-resolved density, then
    # integrate to SOC_DEPTH_M *before* the monthly->yearly aggregation
    # (a pool variable, so aggregate with method="mean" like the others).
    soc_vr = ds["SOIL1C_vr"] + ds["SOIL2C_vr"] + ds["SOIL3C_vr"] + ds["SOIL4C_vr"]
    soc_30cm_monthly = integrate_soil_profile_to_depth(
        soc_vr, ds["levdcmp"].values, SOC_DEPTH_M, lev_dim="levdcmp"
    )
    soc_30cm_yearly = aggregate_monthly_to_yearly(soc_30cm_monthly, method="mean")
    result["SOC_0_30cm"] = weighted_annual(soc_30cm_yearly)

    # Belowground veg C = total - aboveground, to see which side of the
    # TOTVEGC/TOTVEGC_ABG divergence (flagged from the earlier full time
    # series) the change is actually on.
    result["TOTVEGC_BLG"] = result["TOTVEGC"] - result["TOTVEGC_ABG"]

    out = xr.Dataset(result)
    ATTRS = {
        "GPP": ("gC/m^2/yr", "domain-mean GPP"),
        "NPP": ("gC/m^2/yr", "domain-mean NPP"),
        "TOTVEGC": ("gC/m^2", "domain-mean total vegetation C"),
        "TOTVEGC_ABG": ("gC/m^2", "domain-mean aboveground vegetation C"),
        "TOTVEGC_BLG": ("gC/m^2", "domain-mean belowground vegetation C (TOTVEGC - TOTVEGC_ABG)"),
        "TOTSOMC_1m": ("gC/m^2", "domain-mean soil organic C, 0-100 cm"),
        "SOC_0_30cm": ("gC/m^2", "domain-mean soil organic C, 0-30 cm"),
        "NDEP_TO_SMINN": ("gN/m^2/yr", "domain-mean atmospheric N deposition"),
        "SUPPLEMENT_TO_SMINN": ("gN/m^2/yr", "domain-mean supplemental (non-mechanistic) N supply"),
        "SMINN": ("gN/m^2", "domain-mean soil mineral N"),
        "WOOD_HARVESTC": ("gC/m^2/yr", "domain-mean wood harvest C to product pools"),
        "WOOD_HARVESTN": ("gN/m^2/yr", "domain-mean wood harvest N to product pools"),
        "PFT_FIRE_CLOSS": ("gC/m^2/yr", "domain-mean fire C loss"),
        "FAREA_BURNED": ("fraction/yr (approx)", "domain-mean annual burned-area fraction, summed from the per-second rate"),
        "RAIN": ("mm/yr", "domain-mean total rainfall"),
        "SNOW": ("mm/yr", "domain-mean total snowfall (liquid-water-equivalent)"),
        "QRUNOFF": ("mm/yr", "domain-mean total liquid runoff"),
        "EFLX_LH_TOT": ("W/m^2", "domain-mean annual-mean latent heat flux"),
        "FSH": ("W/m^2", "domain-mean annual-mean sensible heat flux"),
    }
    for v, (units, long_name) in ATTRS.items():
        out[v].attrs = {"units": units, "long_name": long_name}
    out.attrs["case"] = CASE
    out.attrs["weighting"] = "area*landfrac, weighted spatial mean over lat/lon"

    for v in out.data_vars:
        vals = out[v].values
        print(f"  {v:16s} n={len(vals)}  first={vals[0]:.4g}  last={vals[-1]:.4g}  "
              f"min={np.nanmin(vals):.4g}  max={np.nanmax(vals):.4g}")

    out_path = os.path.join(OUT_DIR, "annual_timeseries.nc")
    out.to_netcdf(out_path)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
