"""
Side-by-side: raw LUH2 source harvest (native 0.25 deg, from transitions.nc)
vs. the harvfix-downscaled 4km harvest field, same year -- to see directly
whether the 0.25 deg blockiness in the downscaled field is already present,
pixel-for-pixel, in the source.

Reads the GeoTIFFs from extract_annual_harvest_luh2_source.py and
extract_annual_harvest_20yr.py (already rsync'd back).

Run **locally** (needs cartopy):
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_luh2_source_vs_downscaled.py
"""

import os

import numpy as np
import rioxarray as rxr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
YEARS = [1870, 1890, 1910, 1930, 1950, 1970, 1990, 2010]  # 1850 is all-zero, skipped

LON_MIN, LON_MAX = -95.5, -73.5
LAT_MIN, LAT_MAX = 24.5, 38.0


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50) -> BoundaryNorm:
    finite = data[np.isfinite(data)]
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    return BoundaryNorm(edges, ncolors=256)


def load_tif(fname):
    da = rxr.open_rasterio(os.path.join(OUT_DIR, fname)).squeeze("band", drop=True)
    lat = da["y"].values
    lon = da["x"].values
    arr = da.values.astype(float)
    nodata = da.rio.nodata
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr, lat, lon


def panel(ax, arr, lat, lon, title, norm):
    mesh = ax.pcolormesh(lon, lat, arr, cmap="OrRd", norm=norm, shading="auto",
                         transform=ccrs.PlateCarree())
    ax.coastlines(resolution="10m", linewidth=0.8)
    ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor="black")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.5, linestyle="--")
    ax.set_title(title)
    return mesh


def main():
    for yr in YEARS:
        source, slat, slon = load_tif(f"LUH2source_AnnualHarvest_{yr}.tif")
        downscaled, dlat, dlon = load_tif(f"AnnualHarvest_{yr}.tif")

        fig, axes = plt.subplots(
            1, 2, figsize=(13, 6),
            subplot_kw={"projection": ccrs.PlateCarree()},
        )
        mesh_s = panel(
            axes[0], source, slat, slon,
            f"LUH2 source, native 0.25°  ({yr})",
            quantile_boundary_norm(source, n_levels=50),
        )
        fig.colorbar(mesh_s, ax=axes[0], label="Harvest (unitless)",
                     orientation="horizontal", pad=0.05, shrink=0.9)

        mesh_d = panel(
            axes[1], downscaled, dlat, dlon,
            f"Downscaled to 4km (harvfix)  ({yr})",
            quantile_boundary_norm(downscaled, n_levels=50),
        )
        fig.colorbar(mesh_d, ax=axes[1], label="Harvest (unitless)",
                     orientation="horizontal", pad=0.05, shrink=0.9)

        out_path = os.path.join(OUT_DIR, f"LUH2sourceVsDownscaled_{yr}.png")
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
