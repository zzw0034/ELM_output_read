"""
Map the multi-epoch mean of the ESA CCI Biomass v7.0 1 km AGB subset
(Figure 1 observation input; source and subset in
../analysis_process_notes.md §3.1).

Values are shown as delivered: oven-dry woody AGB of trees, Mg ha-1 (not
carbon; x0.47 gives Mg C ha-1). The file stores ocean as 0, not missing, so
ocean and lakes are masked here with Natural Earth 10 m admin-1 polygons
(the lakes-removed variant, already in the local cartopy cache). This land
mask is for display only -- analyses take land from the ELM domain.

Runs locally with the cartopy venv:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \
        code/plot_obs_esacci_agb_v7_mean.py [first_year last_year]
Input (pulled remote -> local, git-ignored):
    _cache/obs/ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0_SEUS_lat24-37.5_lon-95--74.nc
Output: figures/obs/esacci_agb_v7_mean_<years>.png
"""
import datetime
import os
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
import xarray as xr
from matplotlib.colors import BoundaryNorm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NC = os.path.join(ROOT, "_cache/obs/ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0_SEUS_lat24-37.5_lon-95--74.nc")
OUT_DIR = os.path.join(ROOT, "figures/obs")
EXTENT = [-95.0, -74.0, 24.0, 37.5]
LEVELS = np.arange(0, 325, 25)  # Mg/ha, 25 Mg/ha bins, extend="max" above 300


def land_mask(lon2d, lat2d):
    """True where a pixel centre falls inside a Natural Earth admin-1 polygon
    (lakes removed) intersecting the domain."""
    path = shpreader.natural_earth(resolution="10m", category="cultural",
                                   name="admin_1_states_provinces_lakes")
    box = shapely.box(EXTENT[0] - 1, EXTENT[2] - 1, EXTENT[1] + 1, EXTENT[3] + 1)
    geoms = [g for g in shpreader.Reader(path).geometries() if g.intersects(box)]
    land = shapely.intersection(shapely.union_all(geoms), box)
    shapely.prepare(land)
    return shapely.contains_xy(land, lon2d, lat2d)


def main():
    ds = xr.open_dataset(NC, decode_times=False)
    years = np.array([(datetime.date(1990, 1, 1) + datetime.timedelta(days=float(t))).year
                      for t in ds["time"].values])
    if len(sys.argv) == 3:
        y0, y1 = int(sys.argv[1]), int(sys.argv[2])
    else:
        y0, y1 = int(years.min()), int(years.max())
    sel = (years >= y0) & (years <= y1)
    used = years[sel]
    agb = ds["agb"].isel(time=np.where(sel)[0]).astype("float32")  # _FillValue decoded to NaN
    mean = agb.mean("time", skipna=True).values
    lon, lat = ds["lon"].values, ds["lat"].values

    lon2d, lat2d = np.meshgrid(lon, lat)
    is_land = land_mask(lon2d, lat2d)
    shown = np.where(is_land, mean, np.nan)

    land_vals = mean[is_land]
    print(f"epochs used ({used.size}): {' '.join(map(str, used))}")
    print(f"land pixels {is_land.sum()} of {is_land.size}; "
          f"land mean {land_vals.mean():.1f} Mg/ha (unweighted by pixel area); "
          f"zero on land {np.mean(land_vals == 0) * 100:.1f}%; "
          f"p50/p90/p99/max {np.percentile(land_vals, [50, 90, 99]).round(1).tolist()}/{land_vals.max():.0f}")
    print(f"non-land pixels that are nonzero: {np.sum(mean[~is_land] > 0)}")

    cmap = plt.get_cmap("Greens", len(LEVELS))
    cmap.set_bad("#dfe3e8")
    norm = BoundaryNorm(LEVELS, ncolors=cmap.N, extend="max")

    fig = plt.figure(figsize=(10, 6.8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_facecolor("#dfe3e8")
    mesh = ax.pcolormesh(lon, lat, shown, cmap=cmap, norm=norm, shading="auto",
                         transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m",
                                                facecolor="none", edgecolor="#777777", linewidth=0.3))
    ax.set_extent(EXTENT, crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False

    span = f"{used.min()}–{used.max()}" if used.size > 1 else f"{used[0]}"
    note = " (no 2013–2014 maps)" if used.min() < 2013 < used.max() else ""
    ax.set_title(f"ESA CCI Biomass v7.0 aboveground biomass (1 km)\n"
                 f"mean of {used.size} annual maps, {span}{note}", fontsize=11, loc="left")
    cb = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.07, shrink=0.75, aspect=40)
    cb.set_label("Tree woody AGB, oven-dry (Mg ha$^{-1}$); × 0.47 = Mg C ha$^{-1}$")
    cb.ax.text(0.0, -3.9, "Grey: ocean and lakes (Natural Earth 10 m; display mask only, the file stores "
               "ocean as 0).", transform=cb.ax.transAxes, fontsize=8, color="#555555", va="top")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"esacci_agb_v7_mean_{used.min()}-{used.max()}.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
