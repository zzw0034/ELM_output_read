"""
Figure 5 median variant (plot_siting_median.py) for all four SSPs, and slides with two SSPs side by side
(user request 2026-10-06).

Every SSP keeps its OWN area-weighted medians of benefit and composite vulnerability (user decision 2026-10-06), so
the high-benefit half is 50 % of eligible land in every SSP. The benefit colour scale (panel a) is shared: 0 to the
98th percentile of the eligible cells of the four SSPs pooled, so that the same colour means the same MgC/ha on a
slide that shows two SSPs (as for the p80 figures, plot_priority_ssps.py). Composite vulnerability is 0-1 in every SSP.

Writes, for each SSP: the paper-style figure, the single-SSP slide (_ppt) and the scatter of plot_siting_median.py
(with the shared scale); one CSV with the medians and quadrant shares of the four SSPs; and two 16:9 slides with two
SSPs each (left/right halves; per half: a benefit and b vulnerability on top, c quadrants with the scatter inset
below, legend under c), fonts sized for a full 16:9 slide:
    fig5_siting_median_pair_SSP1-1.9_SSP2-4.5_<window>_ppt.png
    fig5_siting_median_pair_SSP3-7.0_SSP5-8.5_<window>_ppt.png

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_siting_median_ssps.py
Inputs: those of plot_siting_median.py for SSP1-1.9, SSP2-4.5, SSP3-7.0 and SSP5-8.5.
"""
import copy
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_siting_median as sm  # noqa: E402

pm, ps = sm.pm, sm.ps
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
PAIRS = [("SSP1-1.9", "SSP2-4.5"), ("SSP3-7.0", "SSP5-8.5")]
F = dict(sup=19, title=13.5, tick=11, cbar=11.5, legend=12, inset_lab=11, inset_tick=10)


def half(sf, a, c, vmax):
    """One SSP in a subfigure: a and b on top, c (with the scatter inset) below, legend under c."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    m, keep, med = c["m"], c["keep"], c["med"]
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~keep, 1.0, np.nan)
    gs = sf.add_gridspec(2, 2, height_ratios=[1, 2.05], hspace=0.3, wspace=0.12, left=0.07, right=0.97, top=0.9, bottom=0.12)

    def map_ax(pos, letter, ttl, step):
        ax = sf.add_subplot(pos, projection=ccrs.PlateCarree())
        ax.set_facecolor(ps.BAD)
        ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
        ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                    edgecolor="#777777", linewidth=0.3))
        ax.set_extent([lon4.min(), lon4.max(), lat4.min(), lat4.max()], crs=ccrs.PlateCarree())
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--",
                          xlocs=range(-93, -73, step), ylocs=range(26, 38, 4))
        gl.top_labels = gl.right_labels = False
        gl.xlabel_style = gl.ylabel_style = {"size": F["tick"]}
        pm.mesh(ax, lon4, lat4, inel, ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
        ax.set_title(f"{letter}  {ttl}", loc="left", fontsize=F["title"], color=ps.INK, fontweight="bold")
        return ax

    def cbar(mm, ax, label, line, extend):
        cb = sf.colorbar(mm, ax=ax, orientation="horizontal", fraction=0.07, pad=0.14, shrink=0.95, extend=extend)
        cb.ax.axvline(line, color="black", lw=2.6)
        cb.set_label(label, fontsize=F["cbar"])
        cb.ax.tick_params(labelsize=F["tick"])

    ax = map_ax(gs[0, 0], "a", "Carbon benefit of RF", 8)
    mm = pm.mesh(ax, lon4, lat4, np.where(keep, c["b"], np.nan), pm.BENEFIT_CMAP, Normalize(0, vmax))
    cbar(mm, ax, f"MgC/ha; median {med['benefit']:.1f}", med["benefit"], "both")
    ax = map_ax(gs[0, 1], "b", "Vulnerability", 8)
    mm = pm.mesh(ax, lon4, lat4, c["vuln"], sm.VULN_CMAP, Normalize(0, 1))
    cbar(mm, ax, f"Mean rank; median {med['vuln']:.3f}", med["vuln"], "neither")

    ax = map_ax(gs[1, :], "c", "Siting quadrants (split at medians)", 4)
    pm.mesh(ax, lon4, lat4, c["quad"], ListedColormap(sm.Q_COLS), Normalize(-0.5, 3.5))
    share = {r["quadrant"]: r["share_pct"] for r in c["rows"]}
    handles = [plt.Rectangle((0, 0), 1, 1, color=sm.Q_COLS[q]) for q in (3, 2, 1, 0)]
    ax.legend(handles, [f"{sm.Q_NAMES[q]} ({share[sm.Q_NAMES[q]]:.0f}%)" for q in (3, 2, 1, 0)], loc="upper center",
              bbox_to_anchor=(0.5, -0.07), ncol=2, fontsize=F["legend"], frameon=False, handlelength=1.4, columnspacing=1.2)
    return ax


def inset(fig, ax, a, c):
    """Square scatter inset over the open Gulf; physical size from the drawn map extent (works inside subfigures)."""
    bb = ax.get_window_extent(fig.canvas.get_renderer())
    hi = 0.27
    axi = ax.inset_axes([0.115, 0.11, hi * bb.height / bb.width, hi])
    axi.set_facecolor("white")
    sm.scatter(axi, c, a, small=True, note=False)
    axi.set_xlabel("Benefit (MgC/ha)", fontsize=F["inset_lab"], labelpad=1)
    axi.set_ylabel("Vulnerability", fontsize=F["inset_lab"], labelpad=1)
    axi.tick_params(labelsize=F["inset_tick"])
    axi.set_yticks([0, 0.5, 1])


def draw_pair(args, cs, pair, vmax):
    fig = plt.figure(figsize=(16, 9), facecolor=ps.SURFACE)
    sfs = fig.subfigures(1, 2, wspace=0.02)
    axes = []
    for sf, ssp in zip(sfs, pair):
        sf.set_facecolor(ps.SURFACE)
        a = args[ssp]
        axes.append((half(sf, a, cs[ssp], vmax), a, cs[ssp]))
        sf.suptitle(f"{ssp}  (RF, {a.years}, 4 km)", fontsize=F["sup"], color=ps.INK, fontweight="bold", y=0.985)
    fig.canvas.draw()
    for ax, a, c in axes:
        inset(fig, ax, a, c)
    out = os.path.join(args[pair[0]].out_dir, f"fig5_siting_median_pair_{pair[0]}_{pair[1]}_{args[pair[0]].years}_ppt.png")
    fig.savefig(out, dpi=200, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    ap = pm.parser()
    ap.add_argument("--benefit", choices=("net", "nofire"), default="net")
    ap.add_argument("--rank", choices=("area", "count"), default="area")
    base = ap.parse_args()
    args, cs = {}, {}
    for ssp in SSPS:
        a = copy.copy(base)
        a.ssp = ssp
        cs[ssp] = sm.compute(a)
        args[ssp] = a
    vmax = float(np.nanpercentile(np.concatenate([cs[s]["b"][cs[s]["keep"]] for s in SSPS]), 98))
    print(f"shared benefit colour scale: 0-{vmax:.1f} MgC/ha (p98 of eligible cells, four SSPs pooled)")
    for ssp in SSPS:
        args[ssp].vmax_b = vmax
        sm.draw(args[ssp], cs[ssp])
        sm.draw_ppt(args[ssp], cs[ssp])
    for pair in PAIRS:
        draw_pair(args, cs, pair, vmax)

    out = os.path.join(base.out_dir, f"fig5_siting_median_ssps_{base.years}.csv")
    with open(out, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["ssp", "median_benefit_MgCha", "median_vuln", "total_benefit_PgC", "quadrant", "share_pct", "benefit_PgC",
                     "mean_benefit_MgCha", "mean_fire_pctyr", "mean_water"])
        for ssp in SSPS:
            c = cs[ssp]
            for r in c["rows"]:
                wr.writerow([ssp, f"{c['med']['benefit']:.4g}", f"{c['med']['vuln']:.4g}", f"{c['total']:.4f}", r["quadrant"],
                             f"{r['share_pct']:.2f}", f"{r['benefit_PgC']:.4f}", f"{r['mean_benefit_MgCha']:.2f}",
                             f"{r['mean_fire_pctyr']:.4f}", f"{r['mean_water']:.4f}"])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
