"""
Extract the ANNUAL (single-year, not cumulative) wood-harvest rate from the
flanduse_timeseries input actually used by this run, every 20 years from
1850, to look directly at the raw forcing field before deciding how to
de-block it (see conversation: candidate fixes are smoothing the coarse
0.25 deg field before downscaling, stochastic patch disaggregation, or a
finer real disturbance product).

Source: landuse.timeseries_SEUS_1_24deg_nlcd2elm_simyr1850-2023_c260723.nc
(the "harvfix" flanduse_timeseries).

Runs on Pathfinder (Slurm). Outputs (native 4km grid, no cartopy -- see
replot step): AnnualHarvest_<year>.png/.tif, unitless (sum of
HARVEST_VH1/VH2/SH1/SH2/SH3, that single year only -- no accumulation).

Usage: python extract_annual_harvest_20yr.py
"""

import os
import sys

import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.plot import plot_2d_map, save_geotiff

LANDUSE_TS_FILE = (
    "/projects/hpcl-cli185/proj-shared/zw5/ELM_makeSurfdata/Make_surface_data/"
    "surfdata_results/landuse.timeseries_SEUS_1_24deg_nlcd2elm_simyr1850-2023_c260723.nc"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

YEARS = [1850, 1870, 1890, 1910, 1930, 1950, 1970, 1990, 2010]
HARVEST_VARS = ["HARVEST_VH1", "HARVEST_VH2", "HARVEST_SH1", "HARVEST_SH2", "HARVEST_SH3"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    f = nc.Dataset(LANDUSE_TS_FILE)
    years = f.variables["YEAR"][:].astype(int).tolist()
    lat = f.variables["LATIXY"][:, 0]     # regular grid: LATIXY varies by row only
    lon = f.variables["LONGXY"][0, :]     # LONGXY varies by column only

    for yr in YEARS:
        ti = years.index(yr)
        total = np.zeros((len(lat), len(lon)))
        for v in HARVEST_VARS:
            total += f.variables[v][ti, :, :]

        print(f"  AnnualHarvest {yr} [unitless]  min={np.nanmin(total):.5f}  "
              f"max={np.nanmax(total):.5f}  mean={np.nanmean(total):.5f}")

        png_path = os.path.join(OUT_DIR, f"AnnualHarvest_{yr}.png")
        tif_path = os.path.join(OUT_DIR, f"AnnualHarvest_{yr}.tif")
        plot_2d_map(
            total, lat, lon,
            var_name="Annual wood harvest",
            title=f"Annual wood harvest — {yr}",
            outfile=png_path,
            cmap="OrRd",
            figsize=(10, 6),
            units="unitless (annual harvested area fraction)",
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
            cbar_location="bottom",
        )
        save_geotiff(lon, lat, total, tif_path)

    f.close()
    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
