"""
Extract cumulative wood-harvest (sum of HARVEST_VH1/VH2/SH1/SH2/SH3, unitless
area fraction) from the flanduse_timeseries input actually used by this run,
at a few snapshot years, to check directly whether the spatial pattern lines
up with the 0.25 deg block pattern seen in TOTVEGC_ABG (aboveground biomass).

Source: landuse.timeseries_SEUS_1_24deg_nlcd2elm_simyr1850-2023_c260723.nc
(the "harvfix" flanduse_timeseries -- see seus_landuse_harvfix_downscaling
memory / user_nl_elm for this case).

Also (re-)extracts single-year TOTVEGC_ABG for the same snapshot years from
the run's own h0 output, so the local comparison script has a same-year
biomass panel to sit next to each cumulative-harvest panel (1850/1950 exist
already from earlier work; 2023 is new here).

Runs on Pathfinder (Slurm). Outputs (native 4km grid, no cartopy -- see
replot step):
  CumHarvest_<year>.png/.tif   -- cumulative harvest, unitless (sum of
                                    annual area fractions from 1850 through
                                    <year> inclusive)
  Biomass_2023.png/.tif        -- TOTVEGC_ABG, kgC/m^2, single-year 2023

Usage: python extract_cumulative_harvest.py
"""

import os
import sys

import numpy as np
import xarray as xr
import netCDF4 as nc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import subtract_month_cftime
from elmtools.plot import plot_2d_map, save_geotiff

# ── Paths ────────────────────────────────────────────────────────────────
CASE = "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC"
RUN_DIR = f"/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/{CASE}/run"
LANDUSE_TS_FILE = (
    "/projects/hpcl-cli185/proj-shared/zw5/ELM_makeSurfdata/Make_surface_data/"
    "surfdata_results/landuse.timeseries_SEUS_1_24deg_nlcd2elm_simyr1850-2023_c260723.nc"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

SNAPSHOT_YEARS = [1850, 1950, 2023]
HARVEST_VARS = ["HARVEST_VH1", "HARVEST_VH2", "HARVEST_SH1", "HARVEST_SH2", "HARVEST_SH3"]


def annual_mean_pool_map(ds: xr.Dataset, var: str) -> xr.DataArray:
    corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
    da = ds.assign_coords(time=corrected)[var]
    true_years = np.array([t.year for t in da["time"].values])
    yearly = []
    for yr in np.unique(true_years):
        yr_mean = da.isel(time=np.where(true_years == yr)[0]).mean(dim="time", skipna=True)
        yearly.append(yr_mean.assign_coords(year=int(yr)))
    return xr.concat(yearly, dim="year")


def biomass_single_year_kgC(year: int) -> np.ndarray:
    f = find_h0_files(RUN_DIR, year_min=year, year_max=year)[0]
    with xr.open_dataset(f, decode_times=True) as ds:
        yearly = annual_mean_pool_map(ds, "TOTVEGC_ABG")
        return yearly.isel(year=0).values / 1000.0


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # ---- cumulative harvest from the flanduse_timeseries input -----------
    f = nc.Dataset(LANDUSE_TS_FILE)
    years = f.variables["YEAR"][:].astype(int).tolist()
    lat = f.variables["LATIXY"][:, 0]     # regular grid: LATIXY varies by row only
    lon = f.variables["LONGXY"][0, :]     # LONGXY varies by column only

    cum = np.zeros((len(lat), len(lon)))
    snapshot_set = set(SNAPSHOT_YEARS)
    for ti, yr in enumerate(years):
        step = np.zeros_like(cum)
        for v in HARVEST_VARS:
            step += f.variables[v][ti, :, :]
        cum += step
        if yr in snapshot_set:
            print(f"  CumHarvest {yr} [unitless]  min={np.nanmin(cum):.4f}  "
                  f"max={np.nanmax(cum):.4f}  mean={np.nanmean(cum):.4f}")
            png_path = os.path.join(OUT_DIR, f"CumHarvest_{yr}.png")
            tif_path = os.path.join(OUT_DIR, f"CumHarvest_{yr}.tif")
            plot_2d_map(
                cum.copy(), lat, lon,
                var_name="Cumulative wood harvest",
                title=f"Cumulative wood harvest, 1850-{yr}",
                outfile=png_path,
                cmap="OrRd",
                figsize=(10, 6),
                units="unitless (sum of annual harvested area fraction)",
                add_coastlines=True,
                add_states=True,
                add_borders=True,
                add_gridlines=True,
                set_extent=True,
                cbar_location="bottom",
            )
            save_geotiff(lon, lat, cum.copy(), tif_path)
    f.close()

    # ---- single-year 2023 biomass, to pair with CumHarvest_2023 ----------
    biomass_2023_kgC = biomass_single_year_kgC(2023)
    print(f"  Biomass 2023 [kgC/m^2]  min={np.nanmin(biomass_2023_kgC):.3f}  "
          f"max={np.nanmax(biomass_2023_kgC):.3f}  mean={np.nanmean(biomass_2023_kgC):.3f}")
    png_path = os.path.join(OUT_DIR, "Biomass_2023.png")
    tif_path = os.path.join(OUT_DIR, "Biomass_2023.tif")
    plot_2d_map(
        biomass_2023_kgC, lat, lon,
        var_name="Aboveground biomass (TOTVEGC_ABG)",
        title="Aboveground biomass — 2023",
        outfile=png_path,
        cmap="viridis",
        figsize=(10, 6),
        units="kgC/m^2",
        add_coastlines=True,
        add_states=True,
        add_borders=True,
        add_gridlines=True,
        set_extent=True,
        cbar_location="bottom",
    )
    save_geotiff(lon, lat, biomass_2023_kgC, tif_path)

    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
