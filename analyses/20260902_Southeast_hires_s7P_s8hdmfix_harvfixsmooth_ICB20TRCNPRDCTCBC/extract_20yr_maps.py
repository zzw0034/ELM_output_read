"""
Extract every-20-years snapshot maps from the smoothed-harvest historical run
20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC.

Why this run exists
-------------------
The previous historical run (20260723_..._harvfix_...) produced a
Biomass_2010.png with visible rectangular patches. We traced them to the
harvest forcing: AnnualHarvest_2010.png showed the same rectangles, because
LUH2 wood harvest is native 0.25 deg and harvfix's area-conservative
downscaling to 4 km preserves each coarse cell as a uniform block. The
forcing was then smoothed (landuse.timeseries_..._smoothHARV_...) and the
historical simulation rerun. This script produces the maps needed to check
whether the blocks are gone.

Outputs (native 4 km grid, one file per variable per year), under outputs/:
  Biomass_<year>.tif        TOTVEGC_ABG annual mean          [kgC/m^2]
  AnnualHarvest_<year>.tif  sum of HARVEST_VH1/VH2/SH1/SH2/SH3 [unitless]
  GPP_<year>.tif            annual total                     [gC/m^2/year]
  NPP_<year>.tif            annual total                     [gC/m^2/year]
  SoilC_0-30cm_<year>.tif   December snapshot                [kgC/m^2]

plus quick-look PNGs. The Pathfinder conda env has no cartopy, so those PNGs
have no state boundaries -- plot_20yr_maps_local.py re-plots the GeoTIFFs on
the Mac with cartopy and with color scales held fixed across years.

Conventions carried over from the 20260723 analysis (see
plot_gpp_npp_soilc_maps.py there for the full rationale):
  - h0 records are stamped on the 1st of the *following* month, so every
    stamp is shifted back one month before day-weighting or year-grouping.
  - Fluxes (GPP/NPP) are day-weighted monthly totals summed to a calendar
    year; pools (TOTVEGC_ABG) get a plain 12-month mean.
  - SOC 0-30 cm integrates SOIL1-4C_vr (gC/m^3) with each layer's exact
    overlap with [0, 0.3 m], taken from DZSOI's cumulative depth. DZSOI is
    written only in the run's first (1850) h0 file.

Runs on Pathfinder via run_extract_20yr_maps.slurm.
"""

import os
import sys

import numpy as np
import netCDF4 as nc
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import (
    flux_to_monthly,
    aggregate_monthly_to_yearly,
    subtract_month_cftime,
)
from elmtools.plot import plot_2d_map, save_geotiff

# ── Paths ─────────────────────────────────────────────────────────────────
CASE = "20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC"
RUN_DIR = f"/scratch/hpcl-cli185/zw5/cime_output_dirs/{CASE}/run"

# the smoothed flanduse_timeseries this case actually used
# (from the case's user_nl_elm)
LANDUSE_TS_FILE = (
    "/projects/hpcl-cli185/proj-shared/zw5/ELM_makeSurfdata/Make_surface_data/"
    "surfdata_results/"
    "landuse.timeseries_SEUS_1_24deg_nlcd2elm_smoothHARV_simyr1850-2023_c260723.nc"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

# every 20 years from the run's first year, plus 2023 (the run's last full
# year) so the series also shows the end state
YEARS = [1850, 1870, 1890, 1910, 1930, 1950, 1970, 1990, 2010, 2023]

FIRST_YEAR = 1850          # h0 file that carries DZSOI
TARGET_DEPTH_M = 0.30
SOIL_POOL_VARS = ["SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]
HARVEST_VARS = ["HARVEST_VH1", "HARVEST_VH2", "HARVEST_SH1", "HARVEST_SH2", "HARVEST_SH3"]


# ── Helpers ──────────────────────────────────────────────────────────────

def shift_time_back_one_month(ds: xr.Dataset) -> xr.Dataset:
    """Relabel h0 records from 'stamped on the 1st of the following month'
    to the true month the average covers."""
    corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
    return ds.assign_coords(time=corrected)


def annual_total_flux(ds: xr.Dataset, var: str) -> np.ndarray:
    """gC/m^2/s monthly records -> that year's gC/m^2/year total."""
    da = shift_time_back_one_month(ds)[var]
    monthly_total = flux_to_monthly(da)                       # gC/m^2/month
    yearly = aggregate_monthly_to_yearly(
        monthly_total, method="sum", time_offset=False        # already shifted
    )
    return yearly.isel(year=0).values


def annual_mean_pool(ds: xr.Dataset, var: str) -> np.ndarray:
    """Pool variable -> plain 12-month mean for that year (not a flux, so no
    day-weighting)."""
    da = shift_time_back_one_month(ds)[var]
    return da.mean(dim="time", skipna=True).values


def december_index(ds: xr.Dataset) -> int:
    """Index of the record whose *true* month is December."""
    shifted = shift_time_back_one_month(ds)
    months = [t.month for t in shifted["time"].values]
    return months.index(12)


def soilc_0_30cm(ds: xr.Dataset, time_index: int, dz: np.ndarray) -> np.ndarray:
    """Integrate SOIL1-4C_vr (gC/m^3) over [0, TARGET_DEPTH_M] using each
    layer's exact overlap with that interval. Returns (lat, lon) in gC/m^2."""
    total_vr = sum(
        ds[v].isel(time=time_index).values for v in SOIL_POOL_VARS
    )                                                          # (levdcmp, lat, lon)

    layer_bottom = np.cumsum(dz, axis=0)
    layer_top = layer_bottom - dz
    overlap = np.clip(np.minimum(layer_bottom, TARGET_DEPTH_M) - layer_top, 0.0, None)

    return np.nansum(total_vr * overlap, axis=0)


def write_panel(data, lat, lon, fname, label, title, units, cmap):
    """Quick-look PNG (no cartopy on Pathfinder) + the GeoTIFF that the local
    re-plot actually consumes."""
    print(f"  {fname:28s} [{units}]  min={np.nanmin(data):10.3f}  "
          f"max={np.nanmax(data):10.3f}  mean={np.nanmean(data):10.3f}")
    plot_2d_map(
        data, lat, lon,
        var_name=label, title=title,
        outfile=os.path.join(OUT_DIR, f"{fname}.png"),
        cmap=cmap, figsize=(10, 6), units=units,
        add_coastlines=True, add_states=True, add_borders=True,
        add_gridlines=True, set_extent=True, cbar_location="bottom",
    )
    save_geotiff(lon, lat, data, os.path.join(OUT_DIR, f"{fname}.tif"))


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # DZSOI lives only in the run's first h0 file
    first_file = find_h0_files(RUN_DIR, year_min=FIRST_YEAR, year_max=FIRST_YEAR)[0]
    with xr.open_dataset(first_file, decode_times=True) as ds_first:
        dz = ds_first["DZSOI"].values                          # (levgrnd, lat, lon), m
        landmask = ds_first["landmask"].values
        lat = ds_first["lat"].values
        lon = ds_first["lon"].values
    land_nan = np.where(landmask == 1, 1.0, np.nan)
    print(f"Grid {lat.size} x {lon.size}; DZSOI from {os.path.basename(first_file)}")

    # ---- model output: biomass, GPP, NPP, SOC 0-30 cm --------------------
    for yr in YEARS:
        matches = find_h0_files(RUN_DIR, year_min=yr, year_max=yr)
        if not matches:
            print(f"  !! no h0 file for {yr}; skipping")
            continue
        print(f"\n{yr}: {os.path.basename(matches[0])}")

        with xr.open_dataset(matches[0], decode_times=True) as ds:
            biomass = annual_mean_pool(ds, "TOTVEGC_ABG") / 1000.0   # kgC/m^2
            gpp = annual_total_flux(ds, "GPP")                       # gC/m^2/year
            npp = annual_total_flux(ds, "NPP")                       # gC/m^2/year
            soc030 = soilc_0_30cm(ds, december_index(ds), dz) / 1000.0  # kgC/m^2

        write_panel(biomass, lat, lon, f"Biomass_{yr}",
                    "Aboveground biomass (TOTVEGC_ABG)",
                    f"Aboveground biomass — {yr}", "kgC/m^2", "viridis")
        write_panel(gpp, lat, lon, f"GPP_{yr}", "GPP",
                    f"GPP — {yr} annual total", "gC/m^2/year", "YlGn")
        write_panel(npp, lat, lon, f"NPP_{yr}", "NPP",
                    f"NPP — {yr} annual total", "gC/m^2/year", "YlGn")
        write_panel(soc030 * land_nan, lat, lon, f"SoilC_0-30cm_{yr}",
                    "Soil organic C (0-30 cm)",
                    f"Soil organic C, 0-30 cm — Dec {yr}", "kgC/m^2", "BrBG")

    # ---- the forcing itself: annual harvest from the smoothed file -------
    print(f"\nAnnual harvest from {os.path.basename(LANDUSE_TS_FILE)}")
    f = nc.Dataset(LANDUSE_TS_FILE)
    lu_years = f.variables["YEAR"][:].astype(int).tolist()
    lu_lat = f.variables["LATIXY"][:, 0]     # regular grid: LATIXY varies by row only
    lu_lon = f.variables["LONGXY"][0, :]     # LONGXY varies by column only

    for yr in YEARS:
        if yr not in lu_years:
            print(f"  !! {yr} not in the landuse timeseries; skipping")
            continue
        ti = lu_years.index(yr)
        total = np.zeros((len(lu_lat), len(lu_lon)))
        for v in HARVEST_VARS:
            total += f.variables[v][ti, :, :]
        write_panel(total, lu_lat, lu_lon, f"AnnualHarvest_{yr}",
                    "Annual wood harvest",
                    f"Annual wood harvest (smoothed) — {yr}",
                    "unitless (annual harvested area fraction)", "OrRd")
    f.close()

    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
