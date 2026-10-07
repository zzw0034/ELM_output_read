"""
Talk slide: how the carbon offset potential is calculated (user requests 2026-10-07), 16:9, large fonts, in the two-panel
style of 20260910_seus_rerun/20260911_seus_halfdeg_dt3600/outputs/future_scenario_cumulative_nbp_split.png, with the
deck's colours (IPCC AR6 SSP colours; RF blue, RH orange, DF deep red as in Figure 2).

  One SSP (SSP2-4.5): cumulative regional NBP since 2024 of Default (solid black, the reference) and RF, RH and DF
  (dashed); the offsets by 2100 are bracketed: RF - Default, RH - Default and Default - DF. DF is paired with the
  crit_dayl_stress = 38000 s Default (blueprint A2), so its bracket value (11.8) is that pair's, while the curve drawn
  is the 36000 s Default (2.33 vs 2.05 PgC by 2100). The four-SSP baseline panel was dropped (user request 2026-10-07);
  the static-baseline over-credit numbers are in notes 3.29.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure2/plot_offset_method_slide.py
Inputs: _cache/figure2/transient_domain_totals_4km.npz, _cache/figure2/future_4km/<SSP>{,_RF,_RH,_cds38000,_DF_cds38000}__totals.npz
Output: figures/figure2/slides/offset_potential_method.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import COLORS, GRID, INK, INK2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "_cache/figure2")
OUT = os.path.join(ROOT, "figures/figure2/slides")
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
SSP_COL = {"SSP1-1.9": "#00adcf", "SSP2-4.5": "#f79420", "SSP3-7.0": "#e71d25", "SSP5-8.5": "#951b1e"}   # IPCC AR6
SHOW = "SSP2-4.5"
HIST0 = 2014


def nbp(name):
    z = np.load(os.path.join(CACHE, "future_4km", f"{name}__totals.npz"), allow_pickle=True)
    yr = z["year"].astype(int)
    assert yr[0] == 2024 and yr[-1] == 2100 and np.all(np.diff(yr) == 1)
    return yr, z["NBP"].astype("f8")


def style(ax, ylab):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=15)
    ax.set_xlabel("year", fontsize=16, color=INK)
    ax.set_ylabel(ylab, fontsize=16, color=INK)
    ax.axhline(0, color=INK2, lw=1)


def bracket(ax, x, y0, y1, text, color):
    ax.annotate("", xy=(x, y1), xytext=(x, y0), arrowprops=dict(arrowstyle="<->", color=color, lw=2.2, shrinkA=0, shrinkB=0))
    ax.text(x + 1.2, (y0 + y1) / 2, text, fontsize=15, color=color, fontweight="bold", va="center")


def main():
    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.045, 0.94, "How the carbon offset potential is calculated", fontsize=30, fontweight="bold", color=INK, va="center")
    fig.text(0.045, 0.865, r"Offset potential $=\sum_{2024}^{t}\,(\mathrm{NBP}_{\mathrm{management}}-\mathrm{NBP}_{\mathrm{counterfactual}})$",
             fontsize=18, color=INK, va="center")
    fig.text(0.58, 0.865, "NBP includes photosynthesis, respiration, fire,\nland use and harvest (via wood products)",
             fontsize=15, color=INK2, va="center", linespacing=1.3)
    axB = fig.add_axes([0.08, 0.13, 0.66, 0.61])

    # B: one SSP with the management runs
    yr, vD = nbp(SHOW)
    x = np.concatenate([[2023], yr])
    c = lambda v: np.concatenate([[0.0], np.cumsum(v)])
    runs = {"RF": nbp(SHOW + "_RF")[1], "RH": nbp(SHOW + "_RH")[1], "DF": nbp(SHOW + "_DF_cds38000")[1]}
    d38 = nbp(SHOW + "_cds38000")[1].sum()
    axB.plot(x, c(vD), color=INK, lw=3.2, label="Default (reference)")
    names = {"RF": "RF (restoration and protection)", "RH": "RH (reduced harvest)", "DF": "DF (deforestation counterfactual)"}
    for k in ("RF", "RH", "DF"):
        axB.plot(x, c(runs[k]), color=COLORS[k], lw=2.8, ls="--", label=names[k])
    style(axB, "Cumulative regional NBP since 2024 (PgC)")
    axB.set_xlim(2023, 2100.5)
    axB.set_xticks([2030, 2050, 2070, 2090])
    eD = vD.sum()
    # offsets by 2100, as brackets just outside the plot (clip_on off)
    for xb, y1, txt, k in ((2103, runs["RF"].sum(), f"RF − Default\n+{runs['RF'].sum() - eD:.1f}", "RF"),
                           (2110, runs["RH"].sum(), f"RH − Default\n+{runs['RH'].sum() - eD:.1f}", "RH"),
                           (2103, runs["DF"].sum(), f"Default − DF\n+{d38 - runs['DF'].sum():.1f}*", "DF")):
        axB.annotate("", xy=(xb, y1), xytext=(xb, eD), annotation_clip=False,
                     arrowprops=dict(arrowstyle="<->", color=COLORS[k], lw=2.2, shrinkA=0, shrinkB=0))
        ty = (eD + y1) / 2 + (1.0 if k == "RF" else 0.0)
        axB.text(xb + 1.2, ty, txt, fontsize=14.5, color=COLORS[k], fontweight="bold", va="center", clip_on=False)
    axB.plot([2100, 2111], [eD, eD], color=INK, lw=1, ls=":", clip_on=False)
    h_, l_ = axB.get_legend_handles_labels()
    axB.legend(h_, ["Default (reference)", "RF  restoration and protection", "RH  reduced harvest", "DF  deforestation counterfactual"],
               loc="center", bbox_to_anchor=(0.62, 0.42), fontsize=15, frameon=False)
    axB.set_title(f"{SHOW}: management runs vs Default (4 km)", fontsize=19, color=INK, pad=12, loc="left")
    fig.text(0.08, 0.03, "* DF is paired with its own Default (crit_dayl_stress = 38000 s).", fontsize=12.5, color=INK2)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "offset_potential_method.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"{SHOW}: RF-Def {runs['RF'].sum() - eD:+.2f}, RH-Def {runs['RH'].sum() - eD:+.2f}, Def38-DF {d38 - runs['DF'].sum():+.2f} PgC")
    print("wrote", p)


if __name__ == "__main__":
    main()
