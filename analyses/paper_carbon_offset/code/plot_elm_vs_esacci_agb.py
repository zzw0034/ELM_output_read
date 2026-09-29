"""
ELM 4 km tree stem carbon (the ESA-matched quantity from
extract_elm_4km_tree_stemc.py) next to ESA CCI v7.0 AGB converted to carbon
(x 0.47), both averaged over the same epochs (2005-2012, 2015-2023).

This is a visual first look, not the Figure 1 evaluation: ESA stays at its
native 1 km, ELM at 4 km, and no common mask or aggregation is applied (see
MANUSCRIPT_BLUEPRINT.md D6 for the quantitative procedure).

Writes two PNGs to figures/obs/:
  elm4km_tree_stemc_mean_<y0>-<y1>.png      ELM alone
  elm4km_vs_esacci_agbC_<y0>-<y1>.png        ELM | ESA x 0.47, shared scale

Runs locally with the cartopy venv, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/plot_elm_vs_esacci_agb.py
Inputs (pulled remote -> local, git-ignored):
    _cache/obs_compare/elm4km_tree_stemc_2005-2023.npz
    _cache/obs/ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0_SEUS_lat24-37.5_lon-95--74.nc
"""
import datetime
import os
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import BoundaryNorm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_obs_esacci_agb_v7_mean import EXTENT, NC as ESA_NC, land_mask  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELM_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm4km_tree_stemc_2005-2023.npz")
OUT_DIR = os.path.join(ROOT, "figures/obs")
CARBON_FRACTION = 0.47          # decided 2026-09-24 (analysis_process_notes §3.1)
GC_M2_TO_MGC_HA = 0.01          # 1 gC/m2 = 0.01 MgC/ha
BAD = "#dfe3e8"


def draw(ax, lon, lat, field, cmap, norm, title):
    ax.set_facecolor(BAD)
    mesh = ax.pcolormesh(lon, lat, field, cmap=cmap, norm=norm, shading="auto",
                         transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m",
                                                facecolor="none", edgecolor="#777777", linewidth=0.3))
    ax.set_extent(EXTENT, crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    ax.set_title(title, fontsize=10.5, loc="left")
    return mesh


def main():
    elm = np.load(ELM_NPZ)
    print(f"ELM source: {elm['case']} ({elm['run_dir']})")
    years = elm["year"].tolist()
    elm_c = np.nanmean(elm["tree_stemc"], axis=0) * GC_M2_TO_MGC_HA
    elm_lon, elm_lat = elm["lon"], elm["lat"]
    w = np.where(np.isfinite(elm_c), elm["area"] * elm["landfrac"], 0.0)

    esa = xr.open_dataset(ESA_NC, decode_times=False)
    esa_years = np.array([(datetime.date(1990, 1, 1) + datetime.timedelta(days=float(t))).year
                          for t in esa["time"].values])
    idx = np.where(np.isin(esa_years, years))[0]
    assert sorted(esa_years[idx].tolist()) == sorted(years), (esa_years[idx], years)
    # Mg/ha dry biomass -> Mg C/ha
    esa_c = esa["agb"].isel(time=idx).astype("float32").mean("time").values * CARBON_FRACTION
    lon_e, lat_e = esa["lon"].values, esa["lat"].values
    lon2d, lat2d = np.meshgrid(lon_e, lat_e)
    is_land = land_mask(lon2d, lat2d)
    esa_c = np.where(is_land, esa_c, np.nan)
    w_e = np.where(is_land, np.cos(np.deg2rad(lat2d)), 0.0)

    def stats(x, wt):
        ok = np.isfinite(x) & (wt > 0)
        return (np.sum(x[ok] * wt[ok]) / np.sum(wt[ok]), np.percentile(x[ok], [50, 90, 99]).round(1).tolist(),
                float(np.nanmax(x[ok])))
    em, ep, ex = stats(elm_c, w)
    om, op, ox = stats(esa_c, w_e)
    print(f"epochs ({len(years)}): {' '.join(map(str, years))}")
    print(f"ELM 4 km tree stem C: area-weighted mean {em:.1f} MgC/ha, p50/p90/p99 {ep}, max {ex:.0f}")
    print(f"ESA x{CARBON_FRACTION}: land mean (cos-lat) {om:.1f} MgC/ha, p50/p90/p99 {op}, max {ox:.0f}")
    print("(different grids and masks; not the Figure 1 statistic)")

    vmax = float(np.ceil(max(np.nanpercentile(elm_c, 99.5), np.nanpercentile(esa_c, 99.5)) / 20) * 20)
    levels = np.linspace(0, vmax, 17)
    cmap = plt.get_cmap("Greens", len(levels))
    cmap.set_bad(BAD)
    norm = BoundaryNorm(levels, ncolors=cmap.N, extend="max")
    span = f"{min(years)}–{max(years)}"
    label = "Mg C ha$^{-1}$"
    os.makedirs(OUT_DIR, exist_ok=True)

    fig = plt.figure(figsize=(10, 6.8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    mesh = draw(ax, elm_lon, elm_lat, elm_c, cmap, norm,
                f"ELM 4 km: tree-PFT stem carbon (LIVESTEMC + DEADSTEMC)\n"
                f"× PFT area fraction, mean of {len(years)} years {span} (no 2013–2014)")
    cb = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.07, shrink=0.75, aspect=40)
    cb.set_label(label)
    out1 = os.path.join(OUT_DIR, f"elm4km_tree_stemc_mean_{min(years)}-{max(years)}.png")
    fig.savefig(out1, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out1}")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6.4), subplot_kw={"projection": ccrs.PlateCarree()})
    draw(axes[0], elm_lon, elm_lat, elm_c, cmap, norm,
         "ELM 4 km: tree-PFT stem C × PFT area fraction")
    mesh = draw(axes[1], lon_e, lat_e, esa_c, cmap, norm,
                f"ESA CCI Biomass v7.0, 1 km: AGB × {CARBON_FRACTION}")
    fig.suptitle(f"Aboveground tree woody carbon, mean of the same {len(years)} years {span} (no 2013–2014)",
                 x=0.05, ha="left", fontsize=12)
    cb = fig.colorbar(mesh, ax=axes, orientation="horizontal", pad=0.08, shrink=0.55, aspect=45)
    cb.set_label(label)
    cb.ax.text(0.0, -3.9, "Native grids, no common mask; grey = ocean/lakes or no vegetation. "
               "Visual comparison only.", transform=cb.ax.transAxes, fontsize=8, color="#555555", va="top")
    out2 = os.path.join(OUT_DIR, f"elm4km_vs_esacci_agbC_{min(years)}-{max(years)}.png")
    fig.savefig(out2, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out2}")


if __name__ == "__main__":
    main()
