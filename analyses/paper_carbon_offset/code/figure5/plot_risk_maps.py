"""
Figure 5 companion (supplement candidate): maps of the two risk components used in the
screen (fire loss and water stress; NBP variability dropped 2026-10-01 because it is mostly fire), RF run, SSP3-7.0, 2091-2100, at 4 km (top) and 0.5 deg (bottom).

Components and thresholds exactly as in plot_priority_selection.py (imported from it):
fire = (NEP - LAND_USE_FLUX - NBP) / TOTECOSYSC (%/yr); water stress = 1 - BTRAN, April-October.
The threshold (black line on
each colour bar) is the area-weighted PCT-th percentile of the 4 km component over the eligible
4 km land, shared by both resolutions. Each panel states the share of its own eligible land above
the threshold (4 km: eligible area; 0.5 deg: the 4 km eligible area inside eligible 0.5 deg
cells, i.e. the area the 0.5 deg screen acts on). Cells outside eligible land are drawn in light
grey, so the map shows where the screen can matter.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_risk_maps.py [--pct 80]
Output: figures/figure5/fig5_risk_maps_<SSP>_<window>.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_selection as ps  # noqa: E402

RAMPS = {"fire": ["#fdeee6", "#f6b48f", "#eb6834", "#b8461b", "#7a2a0c"],
         "water": ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]}
INELIGIBLE = "#ecebe7"


def draw(ax, lon, lat, field, elig, cmap, norm, title):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    ax.set_facecolor(ps.BAD)
    ax.pcolormesh(lon, lat, np.ma.masked_invalid(np.where(elig, np.nan, np.where(np.isfinite(field), 1.0, np.nan))),
                  cmap=ListedColormap([INELIGIBLE]), shading="auto", transform=ccrs.PlateCarree(), rasterized=True)
    mesh = ax.pcolormesh(lon, lat, np.ma.masked_invalid(np.where(elig, field, np.nan)), cmap=cmap, norm=norm,
                         shading="auto", transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#777777", linewidth=0.3))
    ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 7.5}
    ax.set_title(title, loc="left", fontsize=10.5, color=ps.INK, fontweight="bold")
    return mesh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--pct", type=float, default=80)
    ap.add_argument("--cache-4km", default=os.path.join(ps.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ps.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ps.ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ps.ROOT, "figures/figure5"))
    a = ap.parse_args()
    m = ps.build(a)
    elig4 = m["a4"] > 0
    T = {k: ps.wquantile(m["R4"][k][elig4], m["a4"][elig4], a.pct / 100) for k, _ in ps.COMPONENTS}

    import cartopy.crs as ccrs
    nc = len(ps.COMPONENTS)
    fig = plt.figure(figsize=(6.2 * nc + 1.0, 10.6), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, nc, hspace=0.32, wspace=0.12, left=0.05, right=0.985, top=0.92, bottom=0.17)
    for col, (k, label) in enumerate(ps.COMPONENTS):
        v4 = m["R4"][k][elig4]
        vmax = float(np.nanpercentile(v4, 98))
        vmin = 0.0
        norm = Normalize(vmin, vmax)
        cmap = LinearSegmentedColormap.from_list(k, RAMPS[k])
        share4 = 100 * m["a4"][elig4 & (m["R4"][k] > T[k])].sum() / m["a4"].sum()
        ac = m["ac"]
        share5 = 100 * ac[m["ok5"] & (m["R5"][k] > T[k])].sum() / ac[m["ok5"]].sum()
        ax4 = fig.add_subplot(gs[0, col], projection=ccrs.PlateCarree())
        mesh = draw(ax4, m["lon4"], m["lat4"], m["R4"][k], elig4, cmap, norm, f"{'ab'[col]}  4 km: {label}")
        ax5 = fig.add_subplot(gs[1, col], projection=ccrs.PlateCarree())
        draw(ax5, m["lon5"], m["lat5"], m["R5"][k], m["ok5"], cmap, norm, f"{'cd'[col]}  0.5°: {label}")
        for ax, sh in ((ax4, share4), (ax5, share5)):
            ax.text(0.98, 0.03, f"{sh:.0f}% of eligible land\nabove the threshold", transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=8.8, color=ps.INK, bbox=dict(facecolor=ps.SURFACE, edgecolor="none", alpha=0.9, pad=3))
        pos = ax5.get_position()
        cax = fig.add_axes([pos.x0 + 0.03, 0.105, pos.width - 0.06, 0.016])
        cb = fig.colorbar(mesh, cax=cax, orientation="horizontal", extend="max")
        cb.ax.axvline(T[k], color="black", lw=2.2)
        cb.set_label(f"{label}; black line = threshold p{a.pct:g} = {T[k]:.3g}", fontsize=9, color=ps.INK)
        cb.ax.tick_params(labelsize=8.5)
        print(f"{k}: threshold {T[k]:.4g}; eligible land above it {share4:.1f}% (4 km) vs {share5:.1f}% (0.5 deg); "
              f"colour range 0-{vmax:.3g} (4 km p98)")

    fig.suptitle(f"SEUS {a.ssp}, RF, {a.years}: the two risk components of the Figure 5 screen", fontsize=13, color=ps.INK,
                 x=0.04, ha="left", y=0.975)
    fig.text(0.04, 0.012,
             "Fire = (NEP − LAND_USE_FLUX − NBP) / TOTECOSYSC, decade mean (dominated by the 2094–2096 fire years; ~0.5° effective resolution at 4 km because the "
             "population-density\ninput is interpolated from 0.5°). "
             "Water stress = 1 − BTRAN, April–October. Threshold = area-weighted percentile of the 4 km component over eligible land, shared by both resolutions.\n"
             f"Light grey: land outside the eligible area (RF 2060 forest fraction < {a.floor:g}).",
             fontsize=8.5, color=ps.INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, f"fig5_risk_maps_{a.ssp}_{a.years}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
