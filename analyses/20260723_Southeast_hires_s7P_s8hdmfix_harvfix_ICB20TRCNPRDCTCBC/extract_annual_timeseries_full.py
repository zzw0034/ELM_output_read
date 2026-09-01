"""
Domain-mean annual time series of GPP, NPP, biomass (TOTVEGC / TOTVEGC_ABG),
and soil organic C (0-30 cm computed here, 0-100 cm TOTSOMC_1m as-is) for the
full run (1850-2023), to compare against the 0.5 deg downscaled run
(20260901_seus_halfdeg_transient) and check the two resolutions converge to
similar magnitudes/trends.

This case's h0 files are ~12 GB each (324x504 regular lat/lon grid, unlike
the smaller 27x42 grid of the 0.5 deg run) -- unlike
extract_biomass_soc.py's approach (concat several years' worth of a
variable, then reduce), this script processes **one file at a time**:
open, pull out only the handful of needed variables, reduce immediately to
a domain-mean scalar for that year, then discard and move to the next file.
Peak memory is therefore bounded by one file's worth of the selected
variables (~500 MB, dominated by the 4 vertically-resolved SOC pools),
regardless of how many years are processed.

Runs on Pathfinder (Slurm; see run_extract_annual_timeseries_full.slurm).

Usage: python extract_annual_timeseries_full.py
"""

import os
import sys
import time

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import (
    flux_to_monthly,
    integrate_soil_profile_to_depth,
    subtract_month_cftime,
)

CASE = "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC"
RUN_DIR = f"/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/{CASE}/run"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

SOC_DEPTH_M = 0.3
POOL_VARS = ["TOTVEGC", "TOTVEGC_ABG", "TOTSOMC_1m"]
FLUX_VARS = ["GPP", "NPP"]
VR_SOC_VARS = ["SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]


def shift_time_back_one_month(ds: xr.Dataset) -> xr.Dataset:
    corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
    return ds.assign_coords(time=corrected)


def weighted_mean(arr: np.ndarray, weight: np.ndarray) -> float:
    return float(np.nansum(arr * weight) / np.nansum(np.where(np.isfinite(arr), weight, 0.0)))


def process_one_file(path: str, weight: np.ndarray) -> dict:
    with xr.open_dataset(path, decode_times=True) as ds_raw:
        ds = shift_time_back_one_month(ds_raw)

        result = {}
        for v in FLUX_VARS:
            monthly_total = flux_to_monthly(ds[v]).values  # gC/m^2/month, (12,lat,lon)
            annual_total = monthly_total.sum(axis=0)        # gC/m^2/yr
            result[v] = weighted_mean(annual_total, weight)

        for v in POOL_VARS:
            annual_mean = ds[v].mean(dim="time", skipna=True).values  # gC/m^2
            result[v] = weighted_mean(annual_mean, weight)

        soc_vr = ds["SOIL1C_vr"] + ds["SOIL2C_vr"] + ds["SOIL3C_vr"] + ds["SOIL4C_vr"]
        soc_30cm_monthly = integrate_soil_profile_to_depth(
            soc_vr, ds["levdcmp"].values, SOC_DEPTH_M, lev_dim="levdcmp"
        )
        soc_30cm_annual = soc_30cm_monthly.mean(dim="time", skipna=True).values  # gC/m^2
        result["SOC_0_30cm"] = weighted_mean(soc_30cm_annual, weight)

        true_year = int(ds["time"].values[0].year)
    return true_year, result


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    files = find_h0_files(RUN_DIR)
    files = [f for f in files if "1850-01-01" not in os.path.basename(f)]  # skip init snapshot, if present
    print(f"Found {len(files)} h0 files: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}")

    with xr.open_dataset(files[0]) as ds0:
        weight = (ds0["area"].values * ds0["landfrac"].values)
        weight = np.where(np.isfinite(weight), weight, 0.0)

    years, series = [], {v: [] for v in POOL_VARS + FLUX_VARS + ["SOC_0_30cm"]}
    t0 = time.time()
    for i, f in enumerate(files):
        yr, res = process_one_file(f, weight)
        years.append(yr)
        for k, v in res.items():
            series[k].append(v)
        if (i + 1) % 10 == 0 or i == len(files) - 1:
            elapsed = time.time() - t0
            print(f"  [{i+1}/{len(files)}] year={yr}  elapsed={elapsed:.0f}s  "
                  f"GPP={res['GPP']:.1f}  TOTVEGC={res['TOTVEGC']:.1f}  "
                  f"SOC_0_30cm={res['SOC_0_30cm']:.1f}", flush=True)

    out = xr.Dataset(
        {k: (("year",), np.array(v, dtype="float32")) for k, v in series.items()},
        coords={"year": np.array(years, dtype="int32")},
    )
    out["GPP"].attrs = {"units": "gC/m^2/yr", "long_name": "domain-mean GPP"}
    out["NPP"].attrs = {"units": "gC/m^2/yr", "long_name": "domain-mean NPP"}
    out["TOTVEGC"].attrs = {"units": "gC/m^2", "long_name": "domain-mean total vegetation C"}
    out["TOTVEGC_ABG"].attrs = {"units": "gC/m^2", "long_name": "domain-mean aboveground vegetation C"}
    out["TOTSOMC_1m"].attrs = {"units": "gC/m^2", "long_name": "domain-mean soil organic C, 0-100 cm"}
    out["SOC_0_30cm"].attrs = {"units": "gC/m^2", "long_name": "domain-mean soil organic C, 0-30 cm"}
    out.attrs["case"] = CASE
    out.attrs["weighting"] = "area*landfrac, weighted spatial mean over lat/lon"

    out_path = os.path.join(OUT_DIR, "annual_timeseries_full.nc")
    out.to_netcdf(out_path)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
