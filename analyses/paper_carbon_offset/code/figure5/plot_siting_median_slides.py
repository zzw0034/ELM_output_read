"""
Presentation slides for the Figure 5 median variant with the SSP2-4.5 medians as fixed thresholds (notes 3.26; user request
2026-10-06, group-meeting talk, English, 16:9, large fonts). Three slides, all 16 x 9 in at 200 dpi:

  slide_benefit           the RF carbon benefit of SSP2-4.5 as one large map, median marked on the colour bar
  slide_vulnerability     how the composite vulnerability is built: fire risk and water stress (raw values, medians marked)
                          -> each ranked by forest area -> averaged into the composite (large map, median marked)
  slide_summary           the four SSPs split at the SSP2-4.5 medians: share of forest land in each class (100 % stacked)
                          and the carbon benefit each class holds (PgC, stacked, sums to the SSP's total benefit)

Colours and numbers are those of plot_siting_median_ssps.py --fixed-ref SSP2-4.5 (same compute, same shared benefit
colour scale = p98 of the eligible cells of the four SSPs pooled; the class colours are the poster's).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_siting_median_slides.py
Output: figures/figure5/slides/fig5_slide_{benefit,vulnerability,summary}_fixedSSP245.png
"""
import contextlib
import copy
import io
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
REF = "SSP2-4.5"
F = dict(sup=24, title=19, tick=15, cbar=17, note=15, bar_lab=15)


def map_ax(fig, pos, c, title, step=4):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    m, keep = c["m"], c["keep"]
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
    ax.set_facecolor(ps.BAD)
    ax.coastlines(resolution="10m", linewidth=0.6, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#777777", linewidth=0.35))
    ax.set_extent([lon4.min(), lon4.max(), lat4.min(), lat4.max()], crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--",
                      xlocs=range(-93, -73, step), ylocs=range(26, 38, 4))
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": F["tick"]}
    pm.mesh(ax, lon4, lat4, np.where(land4 & ~keep, 1.0, np.nan), ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
    ax.set_title(title, loc="left", fontsize=F["title"], color=ps.INK, fontweight="bold")
    return ax


def cbar(fig, mm, ax, label, line, extend, orientation="horizontal", size=F["cbar"], **kw):
    cb = fig.colorbar(mm, ax=ax, orientation=orientation, extend=extend, **kw)
    (cb.ax.axvline if orientation == "horizontal" else cb.ax.axhline)(line, color="black", lw=3.5)
    cb.set_label(label, fontsize=size)
    cb.ax.tick_params(labelsize=F["tick"])
    return cb


def slide_benefit(c, vmax, out):
    fig = plt.figure(figsize=(16, 9), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(1, 1, left=0.05, right=0.97, top=0.87, bottom=0.1)
    ax = map_ax(fig, gs[0, 0], c, "")
    mm = pm.mesh(ax, c["m"]["lon4"], c["m"]["lat4"], np.where(c["keep"], c["b"], np.nan), pm.BENEFIT_CMAP, Normalize(0, vmax))
    t = c["thr"]["benefit"]
    cbar(fig, mm, ax, f"MgC per ha of forest land  (black line: median {t:.1f})", t, "both", fraction=0.05, pad=0.07, shrink=0.6)
    fig.suptitle(f"Carbon benefit of RF: extra ecosystem carbon vs Default, {REF}", fontsize=F["sup"],
                 color=ps.INK, x=0.05, ha="left", y=0.965)
    fig.text(0.05, 0.905, "Per hectare of forest land (RF 2060 tree fraction ≥ 5 %); net of fire.  "
             f"Half of the forest land lies above the median.", fontsize=F["note"], color=ps.INK2, ha="left")
    fig.savefig(out, dpi=200, facecolor=ps.SURFACE)
    plt.close(fig)


def slide_vulnerability(c, out):
    fig = plt.figure(figsize=(16, 9), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.75], hspace=0.38, wspace=0.24, left=0.04, right=0.97, top=0.86, bottom=0.07)
    lon4, lat4, keep = c["m"]["lon4"], c["m"]["lat4"], c["keep"]
    for row, key, cmap, ttl, lab in ((0, "fire", pm.FIRE_CMAP, "Fire risk", "% of carbon burned per year"),
                                     (1, "water", pm.WATER_CMAP, "Water stress", "1 − BTRAN, Apr–Oct")):
        ax = map_ax(fig, gs[row, 0], c, ttl, step=8)
        vals = np.where(keep, c[key], np.nan)
        mm = pm.mesh(ax, lon4, lat4, vals, cmap, Normalize(0, float(np.nanpercentile(vals[keep], 98))))
        cbar(fig, mm, ax, f"{lab}  (median {c['med'][key]:.2g})", c["med"][key], "max", size=F["tick"],
             fraction=0.07, pad=0.14, shrink=0.95)
    ax = map_ax(fig, gs[:, 1], c, "Composite vulnerability")
    mm = pm.mesh(ax, lon4, lat4, c["vuln"], sm.VULN_CMAP, Normalize(0, 1))
    t = c["thr"]["vuln"]
    cbar(fig, mm, ax, f"Mean rank of fire risk and water stress  (black line: median {t:.2f})", t, "neither",
         fraction=0.05, pad=0.07, shrink=0.9)
    fig.suptitle(f"Vulnerability: fire risk + water stress, combined by rank  ({REF}, RF run)", fontsize=F["sup"],
                 color=ps.INK, x=0.04, ha="left", y=0.965)
    fig.text(0.04, 0.905, "Each component is ranked by forest area (0 = safest, 1 = most exposed); the two ranks are averaged.",
             fontsize=F["note"], color=ps.INK2, ha="left")
    # arrows from the two component maps to the composite
    for y in (0.70, 0.30):
        fig.add_artist(matplotlib.patches.FancyArrowPatch((0.36, y), (0.42, 0.5 + (y - 0.5) * 0.3), transform=fig.transFigure,
                                                         arrowstyle="-|>", mutation_scale=28, lw=2.5, color=ps.INK2))
    fig.text(0.39, 0.5, "rank\n+\naverage", fontsize=F["note"], color=ps.INK2, ha="center", va="center",
             bbox=dict(facecolor=ps.SURFACE, edgecolor="none", pad=2))
    fig.savefig(out, dpi=200, facecolor=ps.SURFACE)
    plt.close(fig)


def slide_summary(cs, out):
    order = (3, 2, 1, 0)                                   # green, orange (high benefit) at the bottom, then light blue, grey
    names = {3: "High benefit, low risk", 2: "High benefit, high risk", 1: "Low benefit, low risk", 0: "Low benefit, high risk"}
    share = {s: {q: r["share_pct"] for q, r in zip(order, cs[s]["rows"])} for s in SSPS}     # rows are in Q order 3, 2, 1, 0
    pgc = {s: {q: r["benefit_PgC"] for q, r in zip(order, cs[s]["rows"])} for s in SSPS}
    for s in SSPS:
        assert [r["quadrant"] for r in cs[s]["rows"]] == [sm.Q_NAMES[q] for q in order]
    fig, axes = plt.subplots(1, 2, figsize=(16, 9), facecolor=ps.SURFACE, gridspec_kw=dict(wspace=0.22))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.17)
    x = np.arange(len(SSPS))
    for ax, data, ylab, ttl, fmt, lab_min in (
            (axes[0], share, "% of forest land", "Share of forest land", "{:.0f}%", 4.0),
            (axes[1], pgc, "PgC", "Carbon benefit held", "{:.2f}", 0.25)):
        ax.set_facecolor(ps.SURFACE)
        bottom = np.zeros(len(SSPS))
        for q in order:
            v = np.array([data[s][q] for s in SSPS])
            ax.bar(x, v, bottom=bottom, width=0.62, color=sm.Q_COLS[q], edgecolor=ps.SURFACE, linewidth=2, label=names[q])
            for i, (vi, bi) in enumerate(zip(v, bottom)):
                if vi >= lab_min:
                    ax.text(x[i], bi + vi / 2, fmt.format(vi), ha="center", va="center", fontsize=F["bar_lab"], color=ps.INK)
            bottom += v
        if ax is axes[1]:
            for i, tot in enumerate(bottom):
                ax.text(x[i], tot + 0.08, f"total {tot:.2f}", ha="center", va="bottom", fontsize=F["bar_lab"], color=ps.INK2)
            ax.set_ylim(0, bottom.max() * 1.1)
        else:
            ax.set_ylim(0, 100)
        ax.set_xticks(x, SSPS, fontsize=F["tick"] + 1)
        ax.tick_params(axis="y", labelsize=F["tick"])
        ax.set_ylabel(ylab, fontsize=F["cbar"])
        ax.set_title(ttl, loc="left", fontsize=F["title"], color=ps.INK, fontweight="bold")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.grid(axis="y", color="#dddddd", lw=0.8)
        ax.set_axisbelow(True)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=F["bar_lab"], frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle(f"All scenarios split at the {REF} medians (RF, 4 km)", fontsize=F["sup"], color=ps.INK,
                 x=0.07, ha="left", y=0.965)
    fig.text(0.07, 0.885, "Fixed thresholds: benefit 41.4 MgC/ha, vulnerability rank 0.49 — so the shares differ between scenarios.",
             fontsize=F["note"], color=ps.INK2, ha="left")
    fig.savefig(out, dpi=200, facecolor=ps.SURFACE)
    plt.close(fig)


def main():
    ap = pm.parser()
    ap.add_argument("--benefit", choices=("net", "nofire"), default="net")
    ap.add_argument("--rank", choices=("area", "count"), default="area")
    base = ap.parse_args([a for a in sys.argv[1:]])
    a = copy.copy(base)
    a.ssp = REF
    with contextlib.redirect_stdout(io.StringIO()):
        ref = sm.compute(a)["ref"]
        cs = {}
        for s in SSPS:
            a = copy.copy(base)
            a.ssp = s
            cs[s] = sm.compute(a, ref)
    vmax = float(np.nanpercentile(np.concatenate([cs[s]["b"][cs[s]["keep"]] for s in SSPS]), 98))
    out_dir = os.path.join(base.out_dir, "slides")
    os.makedirs(out_dir, exist_ok=True)
    paths = [os.path.join(out_dir, f"fig5_slide_{k}_fixedSSP245.png") for k in ("benefit", "vulnerability", "summary")]
    slide_benefit(cs[REF], vmax, paths[0])
    slide_vulnerability(cs[REF], paths[1])
    slide_summary(cs, paths[2])
    for s in SSPS:
        r = {row["quadrant"]: row for row in cs[s]["rows"]}
        print(f"{s}: green {r[sm.Q_NAMES[3]]['share_pct']:.1f}% {r[sm.Q_NAMES[3]]['benefit_PgC']:.3f} PgC; total {cs[s]['total']:.3f} PgC")
    print("wrote", *paths, sep="\n  ")


if __name__ == "__main__":
    main()
