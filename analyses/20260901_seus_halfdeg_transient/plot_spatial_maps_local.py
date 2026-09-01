"""
Spatial QC maps for the 0.5 deg SEUS transient run (20260901_seus_halfdeg_transient):
GPP, biomass (TOTVEGC), and soil organic C (0-30 cm) every 30 years from
1850, plus the run's final year (2023), from extract_spatial_maps.py's
output. One 3-row x 7-column figure, each row sharing a single color scale
across years so panels are directly comparable.

Run **locally** after pulling outputs/spatial_maps_every30yr.nc back from
Pathfinder:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_spatial_maps_local.py
"""

import os

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

CASE = "20260901_seus_halfdeg_transient"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")
NC_PATH = os.path.join(OUT_DIR, "spatial_maps_every30yr.nc")

ROWS = [
    ("GPP", "GPP", "gC/m$^2$/yr", "YlGn", 1.0),
    ("TOTVEGC", "Total veg C (TOTVEGC)", "kgC/m$^2$", "viridis", 1000.0),
    ("TOTVEGC_ABG", "Aboveground veg C (TOTVEGC_ABG)", "kgC/m$^2$", "viridis", 1000.0),
    ("TOTVEGC_BLG", "Belowground veg C (TOTVEGC-ABG)", "kgC/m$^2$", "viridis", 1000.0),
    ("SOC_0_30cm", "Soil organic C, 0-30 cm", "kgC/m$^2$", "BrBG", 1000.0),
]


def main():
    ds = xr.open_dataset(NC_PATH)
    years = ds["year"].values
    lat, lon = ds["lat"].values, ds["lon"].values
    landmask = ds["landmask"].values if "landmask" in ds else None
    land_nan = np.where(landmask == 1, 1.0, np.nan) if landmask is not None else 1.0

    nrows, ncols = len(ROWS), len(years)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(2.6 * ncols, 2.6 * nrows),
        subplot_kw={"projection": ccrs.PlateCarree()},
    )

    for i, (var, label, units, cmap, scale) in enumerate(ROWS):
        stack = (ds[var].values * land_nan) / scale
        vmin, vmax = np.nanmin(stack), np.nanmax(stack)
        meshes = []
        for j, yr in enumerate(years):
            ax = axes[i, j]
            mesh = ax.pcolormesh(
                lon, lat, stack[j], vmin=vmin, vmax=vmax, cmap=cmap,
                shading="auto", transform=ccrs.PlateCarree(),
            )
            meshes.append(mesh)
            ax.coastlines(resolution="50m", linewidth=0.5)
            ax.add_feature(cfeature.STATES, linewidth=0.4, edgecolor="black")
            ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=ccrs.PlateCarree())
            if i == 0:
                ax.set_title(str(yr), fontsize=11)
        cbar = fig.colorbar(meshes[-1], ax=axes[i, :].tolist(), orientation="vertical",
                             fraction=0.02, pad=0.01, shrink=0.9)
        cbar.set_label(f"{label}\n({units})", fontsize=8)

    fig.suptitle(f"{CASE}: spatial maps every 30 yr (row-wise shared color scale)", fontsize=13)

    out_path = os.path.join(OUT_DIR, "spatial_maps_every30yr.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")

    print("\nPer-year land-masked domain range:")
    for var, label, units, _, scale in ROWS:
        stack = (ds[var].values * land_nan) / scale
        for j, yr in enumerate(years):
            arr = stack[j]
            print(f"  {label:28s} {yr}: min={np.nanmin(arr):8.3g} max={np.nanmax(arr):8.3g} "
                  f"mean={np.nanmean(arr):8.3g} {units}")


if __name__ == "__main__":
    main()
