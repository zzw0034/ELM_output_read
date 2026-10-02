"""
Zoom on one region of the Figure 5 selection (20 % budget, no screen), to show why a 4 km high-benefit
patch can be missed by the 0.5 deg selection. Default window: East Tennessee (35-37 N, 85.5-82 W).

  a  4 km benefit per eligible ha (MgC/ha), 0.5 deg cell edges drawn; cells above the 4 km cutoff outlined
  b  0.5 deg run benefit per eligible ha on its cells, each cell labelled with its value; cells selected at
     0.5 deg outlined; the 0.5 deg cutoff (lowest selected value) in the title
  c  selection classes on the 4 km grid: both / 4 km only / 0.5 deg only / eligible, not selected
  d  RF 2060 forest fraction of each 4 km cell (the eligible fraction)
Numbers come from plot_priority_selection.py (imported), so they match Figure 5 exactly.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_selection_zoom.py \\
        [--bbox 35 37 -85.5 -82 --name east_tennessee --budget 20]
Output: figures/figure5/fig5_zoom_<name>_<SSP>_<window>.png
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

N = ps.N
BEN = LinearSegmentedColormap.from_list("ben", ["#f0efec", "#b5dfc6", "#5fbf8e", "#1baf7a", "#0b6e4a"])
FOR = LinearSegmentedColormap.from_list("for", ["#f6f1e7", "#d8c9a3", "#9c8a55", "#5c5328", "#2e2a12"])


def decorate(ax, extent, lon_edges, lat_edges, title):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#333333", linewidth=0.8), zorder=4)
    for x in lon_edges:
        ax.plot([x, x], [lat_edges[0], lat_edges[-1]], color="#0b0b0b", lw=0.6, alpha=0.6, transform=ccrs.PlateCarree(), zorder=5)
    for y in lat_edges:
        ax.plot([lon_edges[0], lon_edges[-1]], [y, y], color="#0b0b0b", lw=0.6, alpha=0.6, transform=ccrs.PlateCarree(), zorder=5)
    gl = ax.gridlines(draw_labels=True, linewidth=0, alpha=0)
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}
    ax.set_title(title, loc="left", fontsize=10.5, color=ps.INK, fontweight="bold")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--budget", type=float, default=20)
    ap.add_argument("--bbox", type=float, nargs=4, default=[35.0, 37.0, -85.5, -82.0], help="lat0 lat1 lon0 lon1 (0.5 deg edges)")
    ap.add_argument("--name", default="east_tennessee")
    ap.add_argument("--cache-4km", default=os.path.join(ps.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ps.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ps.ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ps.ROOT, "figures/figure5"))
    a = ap.parse_args()
    m = ps.build(a)
    w4, w5, _, _ = ps.select(m, a.budget / 100 * m["E"])
    a4, b4 = m["a4"], m["b4"]
    cut4 = float(np.nanmin(b4[w4 >= 1]))
    sel5 = ps.block_sum(w5 * (a4 > 0)) > 0
    cut5 = float(np.nanmin(m["b5"][sel5 & m["ok5"]]))

    la0, la1, lo0, lo1 = a.bbox
    j = np.flatnonzero((m["lat5"] > la0) & (m["lat5"] < la1))
    i = np.flatnonzero((m["lon5"] > lo0) & (m["lon5"] < lo1))
    J, I = slice(j[0], j[-1] + 1), slice(i[0], i[-1] + 1)
    j4, i4 = slice(j[0] * N, (j[-1] + 1) * N), slice(i[0] * N, (i[-1] + 1) * N)
    lon4, lat4, lon5, lat5 = m["lon4"][i4], m["lat4"][j4], m["lon5"][I], m["lat5"][J]
    lon_e = np.append(lon5 - 0.25, lon5[-1] + 0.25)
    lat_e = np.append(lat5 - 0.25, lat5[-1] + 0.25)
    extent = [lon_e[0], lon_e[-1], lat_e[0], lat_e[-1]]
    ok4 = m["ok4"][j4, i4]

    import cartopy.crs as ccrs
    pc = ccrs.PlateCarree()
    fig = plt.figure(figsize=(15, 11.2), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.12, left=0.05, right=0.97, top=0.91, bottom=0.12)
    vmax = float(np.nanpercentile(b4[m["a4"] > 0], 98))
    norm = Normalize(0, vmax)

    ax = fig.add_subplot(gs[0, 0], projection=pc)
    ax.set_facecolor(ps.BAD)
    mb = ax.pcolormesh(lon4, lat4, np.ma.masked_invalid(np.where(ok4, b4[j4, i4], np.nan)), cmap=BEN, norm=norm, shading="auto",
                       transform=pc, rasterized=True)
    ax.contour(lon4, lat4, np.where(ok4, (b4[j4, i4] >= cut4).astype(float), 0), levels=[0.5], colors="#0b0b0b", linewidths=0.7,
               transform=pc, zorder=3)
    decorate(ax, extent, lon_e, lat_e, f"a  4 km benefit; black contour = above the 4 km cutoff ({cut4:.0f})")
    cb = fig.colorbar(mb, ax=ax, orientation="horizontal", fraction=0.045, pad=0.07, shrink=0.85, extend="max")
    cb.set_label("RF − Default, ecosystem carbon per eligible ha (MgC/ha), 2091–2100", fontsize=9)

    ax = fig.add_subplot(gs[0, 1], projection=pc)
    ax.set_facecolor(ps.BAD)
    b5 = np.where(m["ok5"][J, I], m["b5"][J, I], np.nan)
    ax.pcolormesh(lon5, lat5, np.ma.masked_invalid(b5), cmap=BEN, norm=norm, shading="auto", transform=pc, rasterized=True)
    for jj in range(len(lat5)):
        for ii in range(len(lon5)):
            if np.isfinite(b5[jj, ii]):
                s = sel5[J, I][jj, ii]
                ax.text(lon5[ii], lat5[jj], f"{b5[jj, ii]:.0f}", ha="center", va="center", fontsize=10,
                        fontweight="bold" if s else "normal", color=ps.INK, transform=pc, zorder=6)
                if s:
                    ax.add_patch(plt.Rectangle((lon5[ii] - 0.25, lat5[jj] - 0.25), 0.5, 0.5, fill=False, edgecolor="#4a3aa7",
                                               lw=2.6, transform=pc, zorder=7))
    decorate(ax, extent, lon_e, lat_e, f"b  0.5° run benefit; purple box = selected at 0.5° (cutoff {cut5:.0f})")

    ax = fig.add_subplot(gs[1, 0], projection=pc)
    ax.set_facecolor(ps.BAD)
    cls = ps.class_map(m, w4, w5)[j4, i4]
    ax.pcolormesh(lon4, lat4, np.ma.masked_invalid(cls), cmap=ListedColormap(ps.CLS_COLS), norm=Normalize(-0.5, 3.5),
                  shading="auto", transform=pc, rasterized=True)
    decorate(ax, extent, lon_e, lat_e, f"c  Selection at the {a.budget:g}% budget")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ps.CLS_COLS[k]) for k in (3, 1, 2, 0)]
    ax.legend(handles, [ps.CLS_NAMES[k] for k in (3, 1, 2, 0)], loc="lower left", fontsize=8.5, framealpha=0.93, edgecolor="none")

    ax = fig.add_subplot(gs[1, 1], projection=pc)
    ax.set_facecolor(ps.BAD)
    mf = ax.pcolormesh(lon4, lat4, np.ma.masked_invalid(np.where(np.isfinite(b4[j4, i4]) | ok4, m["e4"][j4, i4], np.nan)), cmap=FOR,
                       norm=Normalize(0, 1), shading="auto", transform=pc, rasterized=True)
    decorate(ax, extent, lon_e, lat_e, "d  RF forest fraction in 2060 (eligible fraction)")
    cbf = fig.colorbar(mf, ax=ax, orientation="horizontal", fraction=0.045, pad=0.07, shrink=0.85)
    cbf.set_label("Fraction of the cell's land", fontsize=9)

    fig.suptitle(f"Why a 4 km high-benefit band is missed at 0.5°: {a.name.replace('_', ' ').title()} ({a.ssp}, RF, {a.years})", fontsize=13,
                 color=ps.INK, x=0.05, ha="left", y=0.975)
    fig.text(0.05, 0.015,
             "Grid lines = 0.5° cells. A 0.5° cell is selected only if its own benefit (0.5° run) reaches the 0.5° cutoff; the 4 km map selects every 4 km cell above the 4 km cutoff.\n"
             "Cells where the high-benefit band covers only part of the 0.5° cell average out below the cutoff, so the band is missed at 0.5°. Same selection as Figure 5 "
             "(equal area, 20% of eligible land).",
             fontsize=8.6, color=ps.INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, f"fig5_zoom_{a.name}_{a.ssp}_{a.years}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"cutoffs: 4 km {cut4:.1f}, 0.5 deg {cut5:.1f} MgC/ha; wrote {png}")


if __name__ == "__main__":
    main()
