"""
Talk slide (user request 2026-10-07): the reduced version of Figure 3 (plot_gain_heterogeneity.py, imported for the
data and the statistics), 16:9 with large fonts and four panels:

  a  RF gain, native 4 km run          b  RF gain, native 0.5 deg run (same green scale as the talk's benefit maps)
  c  zoom 1 of Figure 3 (the 0.5 deg cell with the largest within-cell SD of the 4 km gain), 4 km vs 0.5 deg
  d  top 10 % of the land area by gain: both runs / 4 km only (missed by 0.5 deg) / 0.5 deg only; the overlap share
Gain = TOTECOSYSC RF - Default, MgC/ha of land, mean of the window; common support of the two runs, weights area x
landfrac. The 0.5 deg run is a separately configured run, so differences combine resolution and configuration.
Overlap classes avoid green, which means "high benefit, low risk" elsewhere in the talk.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure3/plot_gain_heterogeneity_slide.py [--ssp SSP3-7.0]
Output: figures/figure3/slides/fig3_gain_heterogeneity_slide_<SSP>.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_gain_heterogeneity as fh  # noqa: E402

GREEN = LinearSegmentedColormap.from_list("ben", ["#f0efec", "#b5dfc6", "#5fbf8e", "#1baf7a", "#0b6e4a"])
CLS_COLS = ["#e1e0dc", "#eb6834", "#b9a3d9", "#1c5cab"]          # neither, 4 km only, 0.5 deg only, both
CLS_NAMES = ["Neither", "4 km only (missed by 0.5°)", "0.5° only", "Both"]
F = dict(sup=24, title=17, tick=12.5, cbar=14, legend=13.5, note=15)


def base(ax, extent):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    ax.set_facecolor(fh.BAD)
    ax.coastlines(resolution="10m", linewidth=0.6, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#777777", linewidth=0.35))
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--",
                      xlocs=range(-93, -73, 6), ylocs=range(26, 38, 4))
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": F["tick"]}


def title(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=F["title"], color=fh.INK, fontweight="bold")


def main():
    import cartopy.crs as ccrs
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--cache-4km", default=os.path.join(fh.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(fh.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--out-dir", default=os.path.join(fh.ROOT, "figures/figure3/slides"))
    a = ap.parse_args()
    b = fh.build(a.cache_4km, a.cache_05, a.ssp, "RF", a.years)
    m = b["w"] > 0
    st = fh.stats(b["c"][m], b["a"][m], b["w"][m])
    zooms, med_sd = fh.pick_zooms(b)
    vmax = float(np.ceil(fh.wquantile(b["c"][m], b["w"][m], [0.98])[0] / 10) * 10)
    norm = Normalize(0, vmax)
    c_map = np.where(b["common"], b["c"], np.nan)
    a_map = np.where(np.isfinite(b["a5"]) & (b["wb"] > 0), b["a5"], np.nan)
    extent = [float(b["lon4"].min()), float(b["lon4"].max()), float(b["lat4"].min()), float(b["lat4"].max())]

    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.04, 0.95, "A 0.5° model averages away the hotspots", fontsize=F["sup"] + 4, fontweight="bold", color=fh.INK,
             va="center")
    fig.text(0.04, 0.895, f"RF − Default, ecosystem carbon stock, {a.ssp}, {a.years} mean", fontsize=F["note"], color=fh.INK2,
             va="center")
    PC = ccrs.PlateCarree()
    axa = fig.add_axes([0.035, 0.42, 0.29, 0.39], projection=PC)
    axb = fig.add_axes([0.36, 0.42, 0.29, 0.39], projection=PC)
    for ax, lon, lat, fld, lt, tt in ((axa, b["lon4"], b["lat4"], c_map, "a", "4 km run"),
                                      (axb, b["lon5"], b["lat5"], a_map, "b", "0.5° run")):
        base(ax, extent)
        mm = ax.pcolormesh(lon, lat, np.ma.masked_invalid(fld), cmap=GREEN, norm=norm, shading="auto", transform=PC,
                           rasterized=True)
        title(ax, lt, tt)
    # zoom box on both maps
    j, i = zooms[0]
    j0, j1 = max(j - 1, 0), min(j + 2, len(b["lat5"]))
    i0, i1 = max(i - 1, 0), min(i + 2, len(b["lon5"]))
    for ax in (axa, axb):
        ax.add_patch(Rectangle((b["lon5"][i0] - 0.25, b["lat5"][j0] - 0.25), 0.5 * (i1 - i0), 0.5 * (j1 - j0), fill=False,
                               edgecolor="black", lw=2, transform=PC, zorder=5))
    cax = fig.add_axes([0.09, 0.345, 0.5, 0.022])
    cb = fig.colorbar(mm, cax=cax, orientation="horizontal", extend="both")
    cb.set_label("MgC per ha of land", fontsize=F["cbar"])
    cb.ax.tick_params(labelsize=F["tick"])

    # c: zoom 1, 4 km vs 0.5 deg
    r0, r1, q0, q1 = j0 * fh.N, j1 * fh.N, i0 * fh.N, i1 * fh.N
    lon_e = np.append(b["lon5"][i0:i1] - 0.25, b["lon5"][i1 - 1] + 0.25)
    lat_e = np.append(b["lat5"][j0:j1] - 0.25, b["lat5"][j1 - 1] + 0.25)
    for k, (x0, lon, lat, fld, lab) in enumerate(((0.07, b["lon4"][q0:q1], b["lat4"][r0:r1], c_map[r0:r1, q0:q1], "4 km run"),
                                                  (0.255, b["lon5"][i0:i1], b["lat5"][j0:j1], a_map[j0:j1, i0:i1], "0.5° run"))):
        ax = fig.add_axes([x0, 0.03, 0.17, 0.215])
        ax.pcolormesh(lon, lat, np.ma.masked_invalid(fld), cmap=GREEN, norm=norm, shading="auto", rasterized=True)
        for xx in lon_e:
            ax.axvline(xx, color="black", lw=0.8, alpha=0.6)
        for yy in lat_e:
            ax.axhline(yy, color="black", lw=0.8, alpha=0.6)
        ax.set_xlim(lon_e[0], lon_e[-1])
        ax.set_ylim(lat_e[0], lat_e[-1])
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor(fh.BAD)
        ax.text(0.03, 0.97, lab, transform=ax.transAxes, va="top", fontsize=F["legend"], color=fh.INK,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))
        if k == 0:
            title(ax, "c", "Zoom (black box in a, b)")
    fig.text(0.46, 0.2, f"Inside one 0.5° cell the 4 km gain\nvaries by ±{b['within_sd'][j, i]:.0f} MgC/ha (SD);\na 0.5° model sees one value.",
             fontsize=F["note"] + 1, color=fh.INK, va="center", linespacing=1.4)

    # d: top 10 % overlap
    qc = fh.wquantile(b["c"][m], b["w"][m], [0.9])[0]
    qa = fh.wquantile(b["a"][m], b["w"][m], [0.9])[0]
    topc, topa = b["c"] >= qc, b["a"] >= qa
    cls = np.where(topc & topa, 3, np.where(topc, 1, np.where(topa, 2, 0))).astype("f8")
    cls = np.where(b["common"], cls, np.nan)
    ov = st["top10_overlap"]
    axd = fig.add_axes([0.685, 0.42, 0.29, 0.39], projection=PC)
    base(axd, extent)
    axd.pcolormesh(b["lon4"], b["lat4"], np.ma.masked_invalid(cls), cmap=ListedColormap(CLS_COLS), norm=Normalize(-0.5, 3.5),
                   shading="auto", transform=PC, rasterized=True)
    title(axd, "d", "Top 10 % of the gain")
    fig.text(0.83, 0.17, f"0.5° finds only {100 * ov:.0f} % of the\n4 km top-10 % land", ha="center",
             va="center", fontsize=F["title"] + 1, color=fh.INK, fontweight="bold")
    handles = [plt.Rectangle((0, 0), 1, 1, color=CLS_COLS[k]) for k in (3, 1, 2, 0)]
    axd.legend(handles, [CLS_NAMES[k] for k in (3, 1, 2, 0)], loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2,
               fontsize=F["legend"] - 1, frameon=False, handlelength=1.3, columnspacing=1.0)

    os.makedirs(a.out_dir, exist_ok=True)
    p = os.path.join(a.out_dir, f"fig3_gain_heterogeneity_slide_{a.ssp}.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"{a.ssp} RF: zoom cell SD {b['within_sd'][j, i]:.1f} MgC/ha (median cell {med_sd:.1f}); top-10% overlap {100 * ov:.1f}%; "
          f"colour scale 0-{vmax:.0f}")
    print("wrote", p)


if __name__ == "__main__":
    main()
