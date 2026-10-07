"""
Talk slide: why the baseline must be dynamic (user requests 2026-10-07), 16:9, large fonts, two plots, all four SSPs,
no formulas. Total ecosystem carbon basis:

  dynamic baseline (used):  OP(t) = TOTECOSYSC_RF(t) - TOTECOSYSC_Default(t)
  static baseline:          OP(t) = TOTECOSYSC_RF(t) - TOTECOSYSC at the start of management (2023 annual mean, the
                            end of the shared historical run every future run starts from)

  left   total ecosystem carbon change since 2023 of Default (solid, = the dynamic baseline) and RF (dashed) for the
         four SSPs (IPCC AR6 colours); dashed black at 0 = the static baseline. Default's own rise is what a static
         baseline would also credit to the project.
  right  RF offset in 2100 against the static baseline (hatched) and the dynamic one (solid, SSP colour), with the
         over-crediting of the static baseline (14, 51, 30, 28 %).
TOTECOSYSC includes the wood-product pools in this ELM version.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure2/plot_dynamic_baseline_slide.py
Inputs: _cache/figure2/transient_domain_totals_4km.npz, _cache/figure2/future_4km/<SSP>{,_RF}__totals.npz
Output: figures/figure2/slides/dynamic_baseline.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import GRID, INK, INK2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "_cache/figure2")
OUT = os.path.join(ROOT, "figures/figure2/slides")
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
SSP_COL = {"SSP1-1.9": "#00adcf", "SSP2-4.5": "#f79420", "SSP3-7.0": "#e71d25", "SSP5-8.5": "#951b1e"}   # IPCC AR6


def tec(name):
    z = np.load(os.path.join(CACHE, "future_4km", f"{name}__totals.npz"), allow_pickle=True)
    assert int(z["year"][0]) == 2024 and int(z["year"][-1]) == 2100
    return z["TOTECOSYSC"].astype("f8")


def style(ax, ylab):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=15)
    ax.set_ylabel(ylab, fontsize=16, color=INK)


def main():
    h = np.load(os.path.join(CACHE, "transient_domain_totals_4km.npz"), allow_pickle=True)
    assert int(h["year"][-1]) == 2023
    t0 = float(h["TOTECOSYSC"][-1])
    x = np.arange(2023, 2101)
    D = {s: np.concatenate([[0.0], tec(s) - t0]) for s in SSPS}
    R = {s: np.concatenate([[0.0], tec(s + "_RF") - t0]) for s in SSPS}

    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.045, 0.935, "Why the baseline must be dynamic", fontsize=30, fontweight="bold", color=INK, va="center")

    # left: stock change since the start of management, four SSPs
    ax = fig.add_axes([0.075, 0.2, 0.5, 0.63])
    for s in SSPS:
        ax.plot(x, R[s], color=SSP_COL[s], lw=2.6, ls="--")
        ax.plot(x, D[s], color=SSP_COL[s], lw=2.8)
    ax.axhline(0, color="#555555", lw=3, ls=":", zorder=1)
    ax.set_xlim(2023, 2100)
    ax.set_ylim(-1.3, max(r.max() for r in R.values()) * 1.08)
    ax.set_xticks([2030, 2050, 2070, 2090])
    style(ax, "Total ecosystem carbon, change since 2023 (PgC)")
    ax.set_title("Carbon stock: RF (dashed) and its dynamic baseline, Default (solid)", loc="left", fontsize=17,
                 color=INK2, pad=10)

    # right: RF offset in 2100, static vs dynamic
    axb = fig.add_axes([0.665, 0.2, 0.31, 0.63])
    xi = np.arange(len(SSPS))
    w = 0.38
    for i, s in enumerate(SSPS):
        dyn, sta = R[s][-1] - D[s][-1], R[s][-1]
        axb.bar(xi[i] - w / 2, sta, w, color="white", edgecolor=SSP_COL[s], hatch="//", lw=1.6)
        axb.bar(xi[i] + w / 2, dyn, w, color=SSP_COL[s])
        axb.text(xi[i] - w / 2, sta + 0.12, f"+{100 * (sta - dyn) / dyn:.0f}%", ha="center", va="bottom", fontsize=14,
                 color=INK, fontweight="bold")
        print(f"{s}: RF offset 2100 dynamic {dyn:+.2f}, static {sta:+.2f} PgC, over-credit {100 * (sta - dyn) / dyn:+.0f}%")
    axb.set_xticks(xi, SSPS, fontsize=14)
    axb.set_ylim(0, max(R[s][-1] for s in SSPS) * 1.18)
    style(axb, "RF offset in 2100 (PgC)")
    axb.set_title("Static baseline over-credits RF by", loc="left", fontsize=17, color=INK2, pad=10)

    handles = ([Line2D([], [], color=SSP_COL[s], lw=4, label=s) for s in SSPS] +
               [Line2D([], [], color=INK, lw=2.8, label="Default (dynamic baseline)"),
                Line2D([], [], color=INK, lw=2.6, ls="--", label="RF"),
                Line2D([], [], color="#555555", lw=3, ls=":", label="static baseline (stock in 2023)"),
                Patch(facecolor="white", edgecolor=INK, hatch="//", label="offset vs static baseline"),
                Patch(facecolor=INK2, label="offset vs dynamic baseline")])
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=5, fontsize=13.5, frameon=False,
               columnspacing=1.6, handlelength=2.2)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "dynamic_baseline.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    print("wrote", p)


if __name__ == "__main__":
    main()
