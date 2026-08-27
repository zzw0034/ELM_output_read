"""
Extract the RAW LUH2 source harvest data (native 0.25 deg, global), for the
same years as extract_annual_harvest_20yr.py's downscaled-4km series, to
compare source vs. downscaled side by side.

Source: /projects/hpcl-cli185/proj-shared/zw5/luh/transitions.nc (global
0.25 deg, 720 x 1440, 16 GB -- read only the SEUS-cropped slice per year).
Same variables (primf_harv/primn_harv/secmf_harv/secyf_harv/secnf_harv) and
same year->time-index convention as
ELM_makeSurfdata/Make_surface_data/s4_LUToutput_pft/s4_2_donwscale_LUH2harvest.py:
the file labelled ELM year Y carries LUH2 calendar year Y-1
(LUH2_YEAR0=850, so index = (Y-1) - 850). All target years here are
<=2014 in calendar terms, so all come from this v2h file (no SSP splice
needed).

Runs on Pathfinder (Slurm). Outputs (native 0.25 deg grid, no cartopy --
see replot step): LUH2source_AnnualHarvest_<year>.png/.tif, unitless.

Usage: python extract_annual_harvest_luh2_source.py
"""

import os
import sys

import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.plot import plot_2d_map, save_geotiff

LUH2_PATH = "/projects/hpcl-cli185/proj-shared/zw5/luh/transitions.nc"
LUH2_YEAR0 = 850

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

# same ELM years as extract_annual_harvest_20yr.py
ELM_YEARS = [1850, 1870, 1890, 1910, 1930, 1950, 1970, 1990, 2010]
HARVEST_VARS = ["primf_harv", "primn_harv", "secmf_harv", "secyf_harv", "secnf_harv"]

# same display bbox as the downscaled-4km maps
LON_MIN, LON_MAX = -95.5, -73.5
LAT_MIN, LAT_MAX = 24.5, 38.0


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    f = nc.Dataset(LUH2_PATH)
    lat_raw = f.variables["lat"][:]   # descending, 720
    lon = f.variables["lon"][:]       # ascending, -180..180, 1440

    lat_sort_idx = np.argsort(lat_raw)
    lat = lat_raw[lat_sort_idx]

    lat_mask = (lat >= LAT_MIN) & (lat <= LAT_MAX)
    lon_mask = (lon >= LON_MIN) & (lon <= LON_MAX)
    lat_crop = lat[lat_mask]
    lon_crop = lon[lon_mask]
    # indices into the RAW (descending) lat array that correspond to lat_crop
    lat_raw_idx = lat_sort_idx[lat_mask]
    lon_idx = np.where(lon_mask)[0]

    for elm_year in ELM_YEARS:
        cal_year = elm_year - 1  # E3SM LUT convention, same as harvfix downscaling
        ti = cal_year - LUH2_YEAR0

        total = np.zeros((lat_raw.size, lon.size), dtype=np.float64)
        valid = np.ones((lat_raw.size, lon.size), dtype=bool)
        for v in HARVEST_VARS:
            # netCDF4 auto-masks via the file's "missing_value" attribute
            # (verified: returns a MaskedArray). Track which cells LUH2
            # actually defines (land) vs. masks out (ocean/non-land) --
            # filling masked cells with a bare 0 would make genuine ocean
            # indistinguishable from real "land with zero harvest" later,
            # which matters for e.g. normalized-convolution smoothing.
            raw = f.variables[v][ti, :, :]
            valid &= ~np.ma.getmaskarray(raw)
            total += np.ma.filled(raw, 0.0)
        total[~valid] = np.nan

        # lat_raw_idx already lists rows in ascending-lat order (see above)
        total_crop = total[np.ix_(lat_raw_idx, lon_idx)]

        print(f"  LUH2source AnnualHarvest ELM_year={elm_year} (LUH2 cal_year={cal_year}, "
              f"idx={ti}) [unitless]  min={np.nanmin(total_crop):.5f}  "
              f"max={np.nanmax(total_crop):.5f}  mean={np.nanmean(total_crop):.5f}")

        png_path = os.path.join(OUT_DIR, f"LUH2source_AnnualHarvest_{elm_year}.png")
        tif_path = os.path.join(OUT_DIR, f"LUH2source_AnnualHarvest_{elm_year}.tif")
        plot_2d_map(
            total_crop, lat_crop, lon_crop,
            var_name="Annual wood harvest (LUH2 source, 0.25 deg)",
            title=f"LUH2 source annual wood harvest — cal. year {cal_year} (feeds ELM year {elm_year})",
            outfile=png_path,
            cmap="OrRd",
            figsize=(10, 6),
            units="unitless",
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
            cbar_location="bottom",
        )
        save_geotiff(lon_crop, lat_crop, total_crop, tif_path)

    f.close()
    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
