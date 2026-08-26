"""
Side-by-side comparison: cumulative wood harvest (from the run's own
flanduse_timeseries input) vs. aboveground biomass (TOTVEGC_ABG, model
output), for the same year -- direct visual check of whether the 0.25 deg
block pattern in biomass actually lines up with the harvest forcing's own
spatial pattern, rather than just correlating in timing.

Reads the GeoTIFFs produced by extract_cumulative_harvest.py (already
rsync'd back to this Mac). Where cumulative harvest is high (dark red),
biomass should be low (dark purple) if the block pattern really is
harvest-driven -- that's the thing to look for.

Run **locally** (needs cartopy):
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_harvest_vs_biomass_comparison.py
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

YEAR_PAIRS = [1950, 2023]

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


def panel(ax, arr, lat, lon, title, cmap, norm):
    mesh = ax.pcolormesh(lon, lat, arr, cmap=cmap, norm=norm, shading="auto",
                         transform=ccrs.PlateCarree())
    ax.coastlines(resolution="10m", linewidth=0.8)
    ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor="black")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.5, linestyle="--")
    ax.set_title(title)
    return mesh


def main():
    for yr in YEAR_PAIRS:
        harvest, hlat, hlon = load_tif(f"CumHarvest_{yr}.tif")
        biomass, blat, blon = load_tif(f"Biomass_{yr}.tif")

        fig, axes = plt.subplots(
            1, 2, figsize=(13, 6),
            subplot_kw={"projection": ccrs.PlateCarree()},
        )
        mesh_h = panel(
            axes[0], harvest, hlat, hlon,
            f"Cumulative wood harvest, 1850-{yr}", "OrRd",
            quantile_boundary_norm(harvest, n_levels=50),
        )
        fig.colorbar(mesh_h, ax=axes[0], label="Cumulative harvest (unitless)",
                     orientation="horizontal", pad=0.05, shrink=0.9)

        mesh_b = panel(
            axes[1], biomass, blat, blon,
            f"Aboveground biomass — {yr}", "viridis",
            quantile_boundary_norm(biomass, n_levels=50),
        )
        fig.colorbar(mesh_b, ax=axes[1], label="Biomass (kgC/m^2)",
                     orientation="horizontal", pad=0.05, shrink=0.9)

        out_path = os.path.join(OUT_DIR, f"HarvestVsBiomass_{yr}.png")
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
