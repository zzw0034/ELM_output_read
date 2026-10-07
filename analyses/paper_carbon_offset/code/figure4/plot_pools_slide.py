"""
Talk slide of Figure 4 (user request 2026-10-06): the multi-SSP pool figure reduced to six panels, 16:9 with large fonts.

  a  Default stock by pool, mean of the window, one stacked bar per SSP
  b  signed pool contributions to RF - Default (filled circles) and RH - Default (open diamonds), mean of the window
  c  RF - Default: living vegetation, 2024-2100        d  RH - Default: living vegetation (own y axis)
  e  RF - Default: soil (whole column), 2024-2100     f  RH - Default: soil (whole column), same y axis as e
Same data, pools and closure checks as plot_pool_strata.py (imported) and plot_pools_multi_ssp.py; SSP colours = IPCC AR6.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure4/plot_pools_slide.py
Inputs: _cache/figure2/future_4km/<SSP>[_RF|_RH]__totals.npz
Output: figures/figure4/slides/fig4_pools_slide_4km.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_pool_strata as fp  # noqa: E402

SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
SSP_COL = {"SSP1-1.9": "#00adcf", "SSP2-4.5": "#f79420", "SSP3-7.0": "#e71d25", "SSP5-8.5": "#951b1e"}   # IPCC AR6
F = dict(sup=22, title=16, tick=13, lab=14, legend=13)


def style(ax, ylab):
    ax.set_facecolor(fp.SURFACE)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#e2e2e2", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=F["tick"])
    ax.set_ylabel(ylab, fontsize=F["lab"])


def title(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=F["title"], color=fp.INK, fontweight="bold")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--cache-root", default=os.path.join(fp.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--fig2-cache", default=os.path.join(fp.ROOT, "_cache/figure2/future_4km"))
    ap.add_argument("--out-dir", default=os.path.join(fp.ROOT, "figures/figure4/slides"))
    a = ap.parse_args()
    y0, y1 = (int(v) for v in a.years.split("-"))
    keys = [k for k, _, _ in fp.POOLS]

    D = {}
    for s in SSPS:
        T = fp.traj_deltas(a.fig2_cache, a.cache_root, s)
        yr = T["year"]
        end = (yr >= y0) & (yr <= y1)
        assert end.sum() == y1 - y0 + 1
        D[s] = {"T": T, "yr": yr, "stock": {k: float(T["Def"][0][k][end].mean()) for k in keys},
                "d": {mg: {k: float(T[mg][0][k][end].mean()) for k in keys} for mg in ("RF", "RH")},
                "tot": {mg: float(T[mg][1][end].mean()) for mg in ("RF", "RH")}}
        for mg in ("RF", "RH"):
            assert abs(sum(D[s]["d"][mg].values()) - D[s]["tot"][mg]) < 1e-6 * max(1, abs(D[s]["tot"][mg]))
    print(f"{a.years} mean, PgC: " + "; ".join(
        f"{s} RF total {D[s]['tot']['RF']:+.2f}, RH total {D[s]['tot']['RH']:+.2f}, RF soil {D[s]['d']['RF']['soil']:+.3f}, "
        f"RH soil {D[s]['d']['RH']['soil']:+.3f}" for s in SSPS))

    fig = plt.figure(figsize=(16, 9), facecolor=fp.SURFACE)
    gs = fig.add_gridspec(2, 12, height_ratios=[1.05, 1], hspace=0.5, wspace=3.2, left=0.06, right=0.99, top=0.88, bottom=0.08)

    # a: Default stocks
    ax = fig.add_subplot(gs[0, 0:4])
    for i, s in enumerate(SSPS):
        bottom = 0.0
        for k, name, c in fp.POOLS:
            v = D[s]["stock"][k]
            ax.bar(i, v, 0.62, bottom=bottom, color=c, edgecolor=fp.SURFACE, linewidth=1.5, zorder=3, label=name if i == 0 else None)
            bottom += v
    ax.set_xticks(range(len(SSPS)), [s.replace("SSP", "SSP\n", 0) for s in SSPS], fontsize=F["tick"] - 1)
    style(ax, "Default stock (PgC)")
    ax.set_ylim(0, max(sum(D[s]["stock"].values()) for s in SSPS) * 1.45)
    h, l = ax.get_legend_handles_labels()
    l = [x.replace(" (whole column)", "").replace(" (derived)", "") for x in l]
    ax.legend(h[::-1], l[::-1], frameon=False, fontsize=F["legend"] - 1.5, loc="upper center", ncol=2, handlelength=1.0,
              columnspacing=0.8, handletextpad=0.4)
    title(ax, "a", "Default stock by pool")

    # b: signed pool contributions
    ax = fig.add_subplot(gs[0, 4:12])
    cats = keys + ["total"]
    x = np.arange(len(cats))
    offs = np.linspace(-0.27, 0.27, len(SSPS))
    for j, s in enumerate(SSPS):
        rf = [D[s]["d"]["RF"][k] for k in keys] + [D[s]["tot"]["RF"]]
        rh = [D[s]["d"]["RH"][k] for k in keys] + [D[s]["tot"]["RH"]]
        ax.scatter(x + offs[j] - 0.03, rf, s=110, marker="o", color=SSP_COL[s], zorder=4)
        ax.scatter(x + offs[j] + 0.03, rh, s=90, marker="D", facecolor=fp.SURFACE, edgecolor=SSP_COL[s], linewidth=2, zorder=4)
    for xi in x[:-1]:
        ax.axvline(xi + 0.5, color="#e2e2e2", lw=1, zorder=1)
    ax.axhline(0, color=fp.INK, lw=0.9, zorder=2)
    ax.set_xticks(x, [fp.POOL_SHORT[k] for k in keys] + ["Total"], fontsize=F["tick"])
    style(ax, f"Change vs Default (PgC)\n{a.years} mean")
    ssp_h = [Line2D([], [], marker="o", ls="", color=SSP_COL[s], markersize=10) for s in SSPS]
    mg_h = [Line2D([], [], marker="o", ls="", color=fp.INK2, markersize=10),
            Line2D([], [], marker="D", ls="", markerfacecolor=fp.SURFACE, markeredgecolor=fp.INK2, markeredgewidth=2, markersize=9)]
    ax.legend(ssp_h + mg_h, SSPS + ["RF − Default", "RH − Default"], frameon=False, fontsize=F["legend"], loc="upper left",
              ncol=3, columnspacing=1.0, handletextpad=0.3)
    lo = min(min(D[s]["d"][mg][k] for k in keys) for s in SSPS for mg in ("RF", "RH"))
    hi = max(max(D[s]["tot"]["RF"], *D[s]["d"]["RF"].values()) for s in SSPS)
    ax.set_ylim(lo - 0.12 * (hi - lo), hi + 0.42 * (hi - lo))
    title(ax, "b", "Which pools carry the benefit")

    # c-f: trajectories
    def lines(ax, mg, k, letter, ttl, ylab):
        for s in SSPS:
            ax.plot(D[s]["yr"], D[s]["T"][mg][0][k], color=SSP_COL[s], lw=2.6)
        ax.axhline(0, color=fp.INK, lw=0.9)
        ax.set_xlim(2024, 2100)
        ax.set_xticks([2030, 2060, 2090])
        style(ax, ylab)
        title(ax, letter, ttl)

    axes = [fig.add_subplot(gs[1, 3 * i:3 * i + 3]) for i in range(4)]
    lines(axes[0], "RF", "veg", "c", "RF: vegetation", "Difference vs Default (PgC)")
    lines(axes[1], "RH", "veg", "d", "RH: vegetation", "")
    lines(axes[2], "RF", "soil", "e", "RF: soil", "")
    lines(axes[3], "RH", "soil", "f", "RH: soil", "")
    lo = min(min(D[s]["T"][mg][0]["soil"].min() for s in SSPS) for mg in ("RF", "RH"))
    hi = max(max(D[s]["T"][mg][0]["soil"].max() for s in SSPS) for mg in ("RF", "RH"))
    pad = 0.08 * (hi - lo)
    for ax in axes[2:]:
        ax.set_ylim(lo - pad, hi + pad)                     # RF and RH soil on one y axis
    fig.suptitle("Which carbon pools carry the management benefit (SEUS, 4 km, four SSPs)", fontsize=F["sup"], color=fp.INK,
                 x=0.06, ha="left", y=0.975)
    os.makedirs(a.out_dir, exist_ok=True)
    png = os.path.join(a.out_dir, "fig4_pools_slide_4km.png")
    fig.savefig(png, dpi=200, facecolor=fp.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
