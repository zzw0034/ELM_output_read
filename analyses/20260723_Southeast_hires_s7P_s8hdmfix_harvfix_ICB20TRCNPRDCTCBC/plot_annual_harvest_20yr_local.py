"""
Re-plot the annual (non-cumulative) harvest-rate maps with US state
boundaries, using this Mac's local venv (cartopy). Reads the GeoTIFFs
produced by extract_annual_harvest_20yr.py and already rsync'd back.

Run **locally**:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_annual_harvest_20yr_local.py
"""

import os
import sys

import numpy as np
import rioxarray as rxr
from matplotlib.colors import BoundaryNorm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.plot import plot_2d_map

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
YEARS = [1850, 1870, 1890, 1910, 1930, 1950, 1970, 1990, 2010]


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50) -> BoundaryNorm:
    finite = data[np.isfinite(data)]
    if finite.max() <= 0:
        return None  # all-zero (1850): let plot_2d_map auto-scale
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    if len(edges) < 2:
        return None
    return BoundaryNorm(edges, ncolors=256)


def main():
    for yr in YEARS:
        tif_path = os.path.join(OUT_DIR, f"AnnualHarvest_{yr}.tif")
        da = rxr.open_rasterio(tif_path).squeeze("band", drop=True)
        lat = da["y"].values
        lon = da["x"].values
        arr = da.values.astype(float)
        nodata = da.rio.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)

        norm = quantile_boundary_norm(arr)

        png_path = os.path.join(OUT_DIR, f"AnnualHarvest_{yr}.png")
        plot_2d_map(
            arr, lat, lon,
            var_name="Annual wood harvest",
            title=f"Annual wood harvest — {yr}",
            outfile=png_path,
            cmap="OrRd",
            norm=norm,
            figsize=(10, 6),
            units="unitless",
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
            cbar_location="bottom",
        )


if __name__ == "__main__":
    main()
