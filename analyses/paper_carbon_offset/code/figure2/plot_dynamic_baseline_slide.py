"""
Talk slide: why the baseline must be dynamic (user request 2026-10-07), 16:9, large fonts. Total ecosystem carbon basis:

  dynamic baseline (used):  OP(t) = TOTECOSYSC_management(t) - TOTECOSYSC_Default(t)
  static baseline:          OP(t) = TOTECOSYSC_management(t) - TOTECOSYSC at the start of management

The start of management is the end of the shared historical run (2023 annual mean, the state every future run starts
from). Left: SSP2-4.5 stock change since 2023 of Default and RF, the dynamic offset shaded (blue), Default's own gain
(hatched) which a static baseline would also credit, and the two offsets bracketed in 2100. Right: the two formulas and
a bar chart of both offsets in 2100 for the four SSPs with the over-crediting of the static baseline.
TOTECOSYSC includes the wood-product pools in this ELM version (notes; memory elm_totecosysc_includes_product_pools).

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
from matplotlib.patches import FancyBboxPatch, Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import COLORS, GRID, INK, INK2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "_cache/figure2")
OUT = os.path.join(ROOT, "figures/figure2/slides")
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
SHOW = "SSP2-4.5"
DEF_COL = "#6b6a66"


def tec(name):
    z = np.load(os.path.join(CACHE, "future_4km", f"{name}__totals.npz"), allow_pickle=True)
    assert int(z["year"][0]) == 2024 and int(z["year"][-1]) == 2100
    return z["TOTECOSYSC"].astype("f8")


def main():
    h = np.load(os.path.join(CACHE, "transient_domain_totals_4km.npz"), allow_pickle=True)
    assert int(h["year"][-1]) == 2023
    t0 = float(h["TOTECOSYSC"][-1])                                   # stock at the start of management (end of history)
    res = {}
    for s in SSPS:
        d, r = tec(s), tec(s + "_RF")
        res[s] = (r[-1] - d[-1], r[-1] - t0)                           # dynamic, static offset in 2100 (PgC)

    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.045, 0.935, "Why the baseline must be dynamic", fontsize=30, fontweight="bold", color=INK, va="center")

    # left: SSP2-4.5 stock change since the start of management
    x = np.arange(2023, 2101)
    d = np.concatenate([[0.0], tec(SHOW) - t0])
    r = np.concatenate([[0.0], tec(SHOW + "_RF") - t0])
    ax = fig.add_axes([0.075, 0.12, 0.40, 0.68])
    ax.fill_between(x, d, r, color=COLORS["RF"], alpha=0.18, lw=0)
    ax.fill_between(x, 0, d, color=DEF_COL, alpha=0.16, lw=0, hatch="//", edgecolor=DEF_COL)
    ax.plot(x, r, color=COLORS["RF"], lw=3.4)
    ax.plot(x, d, color=DEF_COL, lw=3.4)
    ax.axhline(0, color=INK, lw=1.8, ls="--")
    for xb, y0, y1, txt, col in ((2102, d[-1], r[-1], f"dynamic\n+{r[-1] - d[-1]:.1f}", COLORS["RF"]),
                                 (2115, 0, r[-1], f"static\n+{r[-1]:.1f}", INK)):
        ax.annotate("", xy=(xb, y1), xytext=(xb, y0), annotation_clip=False,
                    arrowprops=dict(arrowstyle="<->", color=col, lw=2.2, shrinkA=0, shrinkB=0))
        ax.text(xb + 1.0, (y0 + y1) / 2, txt, fontsize=14, color=col, fontweight="bold", va="center", clip_on=False)
    ax.plot([2100, 2103], [d[-1], d[-1]], color=DEF_COL, lw=1, ls=":", clip_on=False)
    ax.plot([2100, 2116], [r[-1], r[-1]], color=COLORS["RF"], lw=1, ls=":", clip_on=False)
    ax.set_xlim(2023, 2100.5)
    ax.set_ylim(-0.6, r.max() * 1.45)
    ax.set_xticks([2030, 2050, 2070, 2090])
    ax.tick_params(labelsize=15)
    ax.set_ylabel("Total ecosystem carbon, change since 2023 (PgC)", fontsize=16, color=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_title(f"Example: {SHOW}, 4 km", loc="left", fontsize=18, color=INK2, pad=10)
    ax.legend(handles=[plt.Line2D([], [], color=COLORS["RF"], lw=3.4, label="RF (management)"),
                       plt.Line2D([], [], color=DEF_COL, lw=3.4, label="Default (dynamic baseline)"),
                       plt.Line2D([], [], color=INK, lw=1.8, ls="--", label="Static baseline (stock at start)"),
                       Patch(facecolor=DEF_COL, alpha=0.3, hatch="//", edgecolor=DEF_COL,
                             label="Gain that happens anyway:\ncounted only by a static baseline")],
              loc="upper left", fontsize=13.5, frameon=False, handlelength=2.2)

    # right: the two definitions
    X = 0.66
    def box(y, head, formula, col, face):
        fig.add_artist(FancyBboxPatch((X - 0.01, y - 0.068), 0.335, 0.125, boxstyle="round,pad=0.006,rounding_size=0.012",
                                      transform=fig.transFigure, facecolor=face, edgecolor="none"))
        fig.text(X, y + 0.025, head, fontsize=17, fontweight="bold", color=col, va="center")
        fig.text(X, y - 0.025, formula, fontsize=17, color=INK, va="center")
    box(0.79, "Dynamic baseline (used here)",
        r"$\mathrm{OP}(t)=C_{\mathrm{mgmt}}(t)-C_{\mathrm{baseline}}(t)$", COLORS["RF"], "#e8f0fb")
    box(0.625, "Static baseline",
        r"$\mathrm{OP}(t)=C_{\mathrm{mgmt}}(t)-C_{\mathrm{mgmt}}(t_{\mathrm{start}})$", INK, "#efefed")
    fig.text(X, 0.51, "C = total ecosystem carbon (incl. wood products);\nbaseline = Default run under the same SSP",
             fontsize=13.5, color=INK2, va="center", linespacing=1.35)

    # right bottom: both offsets in 2100 for the four SSPs
    axb = fig.add_axes([X + 0.035, 0.12, 0.29, 0.29])
    xi = np.arange(len(SSPS))
    w = 0.36
    dyn = np.array([res[s][0] for s in SSPS])
    sta = np.array([res[s][1] for s in SSPS])
    axb.bar(xi - w / 2, sta, w, color="#d6d5d0", edgecolor=DEF_COL, hatch="//", lw=0.8, label="static")
    axb.bar(xi + w / 2, dyn, w, color=COLORS["RF"], label="dynamic")
    for i in range(len(SSPS)):
        axb.text(xi[i] - w / 2, sta[i] + 0.15, f"+{100 * (sta[i] - dyn[i]) / dyn[i]:.0f}%", ha="center", va="bottom",
                 fontsize=13, color=INK, fontweight="bold")
    axb.set_xticks(xi, [s.replace("SSP", "SSP") for s in SSPS], fontsize=13)
    axb.tick_params(axis="y", labelsize=13)
    axb.set_ylim(0, sta.max() * 1.3)
    axb.set_ylabel("RF offset in 2100 (PgC)", fontsize=14, color=INK)
    for sp in ("top", "right"):
        axb.spines[sp].set_visible(False)
    axb.grid(axis="y", color=GRID, lw=1)
    axb.set_axisbelow(True)
    axb.legend(loc="upper left", fontsize=13, frameon=False, ncol=2)
    axb.set_title("A static baseline over-credits RF by", loc="left", fontsize=15, color=INK, pad=8)

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "dynamic_baseline.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"start-of-management stock (2023) {t0:.2f} PgC")
    for s in SSPS:
        print(f"{s}: RF offset 2100 dynamic {res[s][0]:+.2f}, static {res[s][1]:+.2f} PgC, over-credit {100 * (res[s][1] - res[s][0]) / res[s][0]:+.0f}%")
    print("wrote", p)


if __name__ == "__main__":
    main()
