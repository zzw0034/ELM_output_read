"""
Extract ELM aboveground biomass and soil organic carbon (0-100 cm) from the
harvfix historical run, to replace the "ELM" panel in
wildfires/ELM_results4CCSImidmeet's Biomass_comparison.png and
SOC_comparison.png (originally built from a different, older
Southeast-hires run; see plot_Biomass.R / plot_SOC.R in that project).

Runs on Pathfinder (Slurm). Produces, on the run's native ~4 km grid:
  - TOTVEGC_ABG, mean of 2014-2020 annual means   [kgC/m^2]  (aboveground biomass)
  - TOTSOMC_1m,  mean of 2000-2020 annual means   [kgC/m^2]  (SOC, 0-100 cm)

matching the original R scripts' year ranges and units. "Annual mean" is the
mean of the 12 true-month values in a calendar year, after the same 1-month
stamp correction used in plot_gpp_npp_soilc_maps.py (h0 records are stamped
on the 1st of the *following* month). TOTVEGC_ABG/TOTSOMC_1m are pool/state
variables, not fluxes, so a plain time-mean is used (no day-weighted sum) --
matching the "yearly_*_mean.nc" convention used for the original ELM run in
process_all_variables_yearly.py.

The actual comparison plot (which also needs the local ESACCI/SoilGrids/HWSD
observational files under wildfires/ELM_results4CCSImidmeet/otherdata00/) is
built separately, *locally*, by plot_biomass_soc_comparison.py -- pull this
script's output NetCDF back to the Mac first.

Usage: python extract_biomass_soc.py
"""

import os
import sys

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import subtract_month_cftime

# ── Paths ─────────────────────────────────────────────────────────────────
CASE = "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC"
RUN_DIR = f"/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/{CASE}/run"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

SOC_YEAR_MIN, SOC_YEAR_MAX = 2000, 2020
BIOMASS_YEAR_MIN, BIOMASS_YEAR_MAX = 2014, 2020

VARS = ["TOTVEGC_ABG", "TOTSOMC_1m"]


# ── Helpers (same conventions as plot_gpp_npp_soilc_maps.py) ──────────────

def load_yearly_vars(files: list[str], varnames: list[str]) -> xr.Dataset:
    """Open each year's h0 file, keep only *varnames*, and concat along
    time. Avoids xr.open_mfdataset: the make_surfdata_pf conda env has no
    dask, and these variables are small enough to just load and concat."""
    per_var = {v: [] for v in varnames}
    for f in files:
        with xr.open_dataset(f, decode_times=True) as ds:
            for v in varnames:
                per_var[v].append(ds[v].load())
    return xr.Dataset({v: xr.concat(das, dim="time") for v, das in per_var.items()})


def shift_time_back_one_month(ds: xr.Dataset) -> xr.Dataset:
    """Relabel h0 records from 'stamped on 1st of following month' to the
    true month the average covers."""
    corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
    return ds.assign_coords(time=corrected)


def annual_mean_map(ds: xr.Dataset, var: str) -> xr.DataArray:
    """Pool/state variable, monthly records -> per-calendar-year mean,
    dims (year, lat, lon). Plain time-mean (no day-weighting -- these are
    not fluxes)."""
    da = shift_time_back_one_month(ds)[var]
    true_years = np.array([t.year for t in da["time"].values])
    yearly = []
    for yr in np.unique(true_years):
        yr_mean = da.isel(time=np.where(true_years == yr)[0]).mean(dim="time", skipna=True)
        yearly.append(yr_mean.assign_coords(year=int(yr)))
    return xr.concat(yearly, dim="year")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    files = find_h0_files(RUN_DIR, year_min=SOC_YEAR_MIN, year_max=SOC_YEAR_MAX)
    print(f"Found {len(files)} h0 files for {SOC_YEAR_MIN}-{SOC_YEAR_MAX}")
    assert len(files) == SOC_YEAR_MAX - SOC_YEAR_MIN + 1, "expected one h0 file per year"

    ds = load_yearly_vars(files, VARS)
    lat = ds["lat"].values
    lon = ds["lon"].values

    veg_yearly = annual_mean_map(ds, "TOTVEGC_ABG")   # gC/m^2, dims (year, lat, lon)
    soc_yearly = annual_mean_map(ds, "TOTSOMC_1m")    # gC/m^2

    biomass_mean = (
        veg_yearly.sel(year=slice(BIOMASS_YEAR_MIN, BIOMASS_YEAR_MAX))
        .mean(dim="year", skipna=True) / 1000.0        # kgC/m^2
    )
    soc_mean = soc_yearly.mean(dim="year", skipna=True) / 1000.0  # kgC/m^2

    print(f"  TOTVEGC_ABG {BIOMASS_YEAR_MIN}-{BIOMASS_YEAR_MAX} mean [kgC/m^2]  "
          f"min={float(biomass_mean.min()):.3f}  max={float(biomass_mean.max()):.3f}  "
          f"mean={float(biomass_mean.mean()):.3f}")
    print(f"  TOTSOMC_1m  {SOC_YEAR_MIN}-{SOC_YEAR_MAX} mean [kgC/m^2]  "
          f"min={float(soc_mean.min()):.3f}  max={float(soc_mean.max()):.3f}  "
          f"mean={float(soc_mean.mean()):.3f}")

    out = xr.Dataset(
        {
            "TOTVEGC_ABG_mean": (("lat", "lon"), biomass_mean.values.astype("float32")),
            "TOTSOMC_1m_mean": (("lat", "lon"), soc_mean.values.astype("float32")),
        },
        coords={"lat": lat, "lon": lon},
    )
    out["TOTVEGC_ABG_mean"].attrs = {
        "units": "kgC/m^2",
        "long_name": f"TOTVEGC_ABG, {BIOMASS_YEAR_MIN}-{BIOMASS_YEAR_MAX} mean of annual means",
    }
    out["TOTSOMC_1m_mean"].attrs = {
        "units": "kgC/m^2",
        "long_name": f"TOTSOMC_1m, {SOC_YEAR_MIN}-{SOC_YEAR_MAX} mean of annual means",
    }
    out.attrs["case"] = CASE

    out_path = os.path.join(OUT_DIR, "ELM_biomass_soc_for_comparison.nc")
    out.to_netcdf(out_path)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
