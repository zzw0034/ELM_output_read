"""
Spatial QC maps for the 0.5 deg SEUS transient run (20260901_seus_halfdeg_transient):
single-year snapshots of GPP, biomass (TOTVEGC, TOTVEGC_ABG, and the
belowground remainder TOTVEGC-TOTVEGC_ABG), and soil organic C (0-30 cm)
every 30 years from the run's start (1850, 1880, 1910, 1940, 1970, 2000),
plus the run's final year (2023) as an endpoint.

TOTVEGC_ABG and the belowground split were added after the domain-mean time
series showed TOTVEGC roughly flat over the run while TOTVEGC_ABG alone
dropped ~22% -- these maps are meant to show *where* the aboveground decline
and belowground gain are each happening, rather than just that they cancel
in the domain mean.

Domain is small (27x42, regular lat/lon), so this opens one h0 file per
target year directly rather than concatenating the full series -- cheap
enough to run without Slurm.

Soil depths: SOIL1C_vr..SOIL4C_vr are carbon density (gC/m^3) on levdcmp
layers. Layer thickness is derived from each file's own levdcmp node depths
via elmtools.process.integrate_soil_profile_to_depth (the standard ELM/CLM
recursive formula), not from the DZSOI variable, since DZSOI is written only
once, in the run's very first (1850-01-01, single-timestep) file. The
formula was cross-checked against that file's own DZSOI and matches exactly
(see extract_annual_timeseries.py in this same folder).

Usage: python extract_spatial_maps.py
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
    subtract_month_cftime,
)

CASE = "20260901_seus_halfdeg_transient"
RUN_DIR = f"/scratch/hpcl-cli185/zw5/cime_output_dirs/{CASE}/run"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

YEARS = [1850, 1880, 1910, 1940, 1970, 2000, 2023]
SOC_DEPTH_M = 0.3
VARS = ["GPP", "TOTVEGC", "SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]


def shift_time_back_one_month(ds: xr.Dataset) -> xr.Dataset:
    corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
    return ds.assign_coords(time=corrected)


def year_maps(year: int) -> dict[str, np.ndarray]:
    # 1850 has two matches: the run's very first h0 file (1850-01-01) is a
    # one-off single-timestep initial-state dump (see module docstring's
    # sibling note in extract_annual_timeseries.py), not the 12-month bundle
    # we want -- pick the file with 12 time records.
    candidates = find_h0_files(RUN_DIR, year_min=year, year_max=year)
    picked = None
    for c in candidates:
        with xr.open_dataset(c) as probe:
            if probe.sizes.get("time", 0) == 12:
                picked = c
                break
    assert picked is not None, f"no 12-month h0 bundle found for {year} among {candidates}"
    with xr.open_dataset(picked, decode_times=True) as ds:
        ds = shift_time_back_one_month(ds)

        gpp_monthly = flux_to_monthly(ds["GPP"])                      # gC/m^2/month
        gpp_annual = aggregate_monthly_to_yearly(
            gpp_monthly, method="sum", time_offset=False
        ).isel(year=0).values                                          # gC/m^2/yr

        totvegc_annual = ds["TOTVEGC"].mean(dim="time", skipna=True).values  # gC/m^2
        totvegc_abg_annual = ds["TOTVEGC_ABG"].mean(dim="time", skipna=True).values  # gC/m^2

        soc_vr = ds["SOIL1C_vr"] + ds["SOIL2C_vr"] + ds["SOIL3C_vr"] + ds["SOIL4C_vr"]
        soc_30cm_monthly = integrate_soil_profile_to_depth(
            soc_vr, ds["levdcmp"].values, SOC_DEPTH_M, lev_dim="levdcmp"
        )
        soc_30cm_annual = soc_30cm_monthly.mean(dim="time", skipna=True).values  # gC/m^2

        landmask = ds["landmask"].values if "landmask" in ds else None

    return {
        "GPP": gpp_annual,
        "TOTVEGC": totvegc_annual,
        "TOTVEGC_ABG": totvegc_abg_annual,
        "TOTVEGC_BLG": totvegc_annual - totvegc_abg_annual,
        "SOC_0_30cm": soc_30cm_annual,
        "landmask": landmask,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    probe_files = find_h0_files(RUN_DIR, year_min=YEARS[0], year_max=YEARS[0])
    with xr.open_dataset(probe_files[0], decode_times=True) as ds0:
        lat = ds0["lat"].values
        lon = ds0["lon"].values

    stacks = {k: [] for k in ["GPP", "TOTVEGC", "TOTVEGC_ABG", "TOTVEGC_BLG", "SOC_0_30cm"]}
    landmask = None
    for yr in YEARS:
        print(f"Processing year {yr} ...")
        m = year_maps(yr)
        for k in stacks:
            stacks[k].append(m[k])
        if landmask is None:
            landmask = m["landmask"]
        print(f"  GPP min={np.nanmin(m['GPP']):.1f} max={np.nanmax(m['GPP']):.1f}  "
              f"TOTVEGC min={np.nanmin(m['TOTVEGC']):.1f} max={np.nanmax(m['TOTVEGC']):.1f}  "
              f"TOTVEGC_ABG min={np.nanmin(m['TOTVEGC_ABG']):.1f} max={np.nanmax(m['TOTVEGC_ABG']):.1f}  "
              f"TOTVEGC_BLG min={np.nanmin(m['TOTVEGC_BLG']):.1f} max={np.nanmax(m['TOTVEGC_BLG']):.1f}  "
              f"SOC_0_30cm min={np.nanmin(m['SOC_0_30cm']):.1f} max={np.nanmax(m['SOC_0_30cm']):.1f}")

    out = xr.Dataset(
        {k: (("year", "lat", "lon"), np.stack(v).astype("float32")) for k, v in stacks.items()},
        coords={"year": YEARS, "lat": lat, "lon": lon},
    )
    if landmask is not None:
        out["landmask"] = (("lat", "lon"), landmask.astype("float32"))
    out["GPP"].attrs = {"units": "gC/m^2/yr", "long_name": "annual total GPP"}
    out["TOTVEGC"].attrs = {"units": "gC/m^2", "long_name": "annual mean total vegetation C"}
    out["TOTVEGC_ABG"].attrs = {"units": "gC/m^2", "long_name": "annual mean aboveground vegetation C"}
    out["TOTVEGC_BLG"].attrs = {"units": "gC/m^2", "long_name": "annual mean belowground vegetation C (TOTVEGC - TOTVEGC_ABG)"}
    out["SOC_0_30cm"].attrs = {"units": "gC/m^2", "long_name": "annual mean soil organic C, 0-30 cm"}
    out.attrs["case"] = CASE

    out_path = os.path.join(OUT_DIR, "spatial_maps_every30yr.nc")
    out.to_netcdf(out_path)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
