"""
Re-plot the harvfix GPP/NPP/SoilC showcase maps with US state boundaries.

The Pathfinder conda env used for the Slurm job (make_surfdata_pf) has no
cartopy, so plot_gpp_npp_soilc_maps.py fell back to plain matplotlib axes
(no coastlines/state borders). This script re-reads the GeoTIFFs that job
already produced (and that were rsync'd back to this Mac) and re-saves the
PNGs using elmtools.plot.plot_2d_map's cartopy path, which this Mac's local
venv supports.

Run **locally** (not via ssh/Slurm) with the local venv that has cartopy:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python replot_with_states_local.py
"""

import os
import sys

import numpy as np
import rioxarray as rxr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.plot import plot_2d_map

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
CASE = "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC"

PANELS = [
    {"fname": "GPP_2014-2023mean", "label": "GPP", "units": "gC/m^2/year", "cmap": "YlGn",
     "title": f"GPP — 2014-2023 mean annual total\n{CASE}"},
    {"fname": "NPP_2014-2023mean", "label": "NPP", "units": "gC/m^2/year", "cmap": "YlGn",
     "title": f"NPP — 2014-2023 mean annual total\n{CASE}"},
    {"fname": "SoilC_0-30cm_2023", "label": "Soil organic C (0-30 cm)", "units": "kgC/m^2", "cmap": "YlOrBr",
     "title": f"Soil organic C, 0-30 cm — end of run (Dec 2023)\n{CASE}"},
    {"fname": "SoilC_fullprofile_2023", "label": "Soil organic C (full profile)", "units": "kgC/m^2", "cmap": "YlOrBr",
     "title": f"Soil organic C, full profile — end of run (Dec 2023)\n{CASE}"},
]


def main():
    for p in PANELS:
        tif_path = os.path.join(OUT_DIR, f"{p['fname']}.tif")
        da = rxr.open_rasterio(tif_path).squeeze("band", drop=True)
        lat = da["y"].values
        lon = da["x"].values
        arr = da.values.astype(float)
        nodata = da.rio.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)

        png_path = os.path.join(OUT_DIR, f"{p['fname']}.png")
        plot_2d_map(
            arr, lat, lon,
            var_name=p["label"],
            title=p["title"],
            outfile=png_path,
            cmap=p["cmap"],
            figsize=(10, 6),
            units=p["units"],
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
        )


if __name__ == "__main__":
    main()
