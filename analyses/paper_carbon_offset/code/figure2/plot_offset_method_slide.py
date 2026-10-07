"""
Talk slide: how the carbon offset potential is calculated (user request 2026-10-07), 16:9, large fonts.

Left: SSP2-4.5 cumulative regional NBP since 2024 of Default and RF (4 km), the offset potential RF - Default shaded
between them, and a static 2024 baseline (zero change) to show what a fixed baseline would over-credit (the carbon
Default gains anyway). Right: the definition and the accounting points. Bottom right: the static-baseline
over-crediting for the four SSPs, on the same cumulative-NBP basis as the Figure 2 benefits (RF - Default by 2100:
3.73, 4.46, 5.21, 5.31 PgC; Default's own cumulative NBP 0.49, 2.33, 1.49, 1.45 PgC -> 13, 52, 29, 27 %).

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure2/plot_offset_method_slide.py
Inputs: _cache/figure2/future_4km/<SSP>{,_RF}__totals.npz (annual regional totals, PgC/yr for NBP)
Output: figures/figure2/slides/offset_potential_method.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import COLORS, GRID, INK, INK2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "_cache/figure2/future_4km")
OUT = os.path.join(ROOT, "figures/figure2/slides")
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
SHOW = "SSP2-4.5"
DEF_COL = "#6b6a66"


def cum_nbp(ssp, sfx=""):
    z = np.load(os.path.join(CACHE, f"{ssp}{sfx}__totals.npz"), allow_pickle=True)
    yr = z["year"].astype(int)
    assert yr[0] == 2024 and np.all(np.diff(yr) == 1)
    # cumulative to the end of each year, starting from 0 at the start of 2024
    return np.concatenate([[2024], yr + 1]), np.concatenate([[0.0], np.cumsum(z["NBP"].astype("f8"))])


def main():
    over = {}
    for s in SSPS:
        _, d = cum_nbp(s)
        _, r = cum_nbp(s, "_RF")
        over[s] = (r[-1] - d[-1], d[-1], 100 * d[-1] / (r[-1] - d[-1]))
    x, d = cum_nbp(SHOW)
    _, r = cum_nbp(SHOW, "_RF")

    fig = plt.figure(figsize=(16, 9), facecolor="white")
    fig.text(0.04, 0.935, "How the carbon offset potential is calculated", fontsize=30, fontweight="bold", color=INK, va="center")
    ax = fig.add_axes([0.07, 0.13, 0.45, 0.70])
    ax.fill_between(x, d, r, color=COLORS["RF"], alpha=0.18, lw=0)
    ax.fill_between(x, 0, d, color=DEF_COL, alpha=0.18, lw=0, hatch="//", edgecolor=DEF_COL)
    ax.plot(x, r, color=COLORS["RF"], lw=3.5)
    ax.plot(x, d, color=DEF_COL, lw=3.5)
    ax.axhline(0, color=INK, lw=1.8, ls="--")
    ax.set_xlim(2024, 2112)
    ax.set_ylim(-0.6, r.max() * 1.12)
    ax.set_xticks([2030, 2050, 2070, 2090])
    ax.tick_params(labelsize=16)
    ax.set_ylabel(f"Cumulative regional NBP since 2024 (PgC)", fontsize=17, color=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_title(f"Example: {SHOW}, 4 km", loc="left", fontsize=19, color=INK2, pad=10)
    # end labels
    ax.text(2101.5, r[-1], f"RF  {r[-1]:+.1f}", fontsize=17, color=COLORS["RF"], fontweight="bold", va="center")
    ax.text(2101.5, d[-1], f"Default  {d[-1]:+.1f}", fontsize=17, color=DEF_COL, fontweight="bold", va="center")
    ax.text(2101.5, 0, "static\nbaseline", fontsize=15, color=INK, va="center")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=COLORS["RF"], alpha=0.25, label=f"Offset potential = RF − Default  (+{r[-1] - d[-1]:.1f} PgC by 2100)"),
                       Patch(facecolor=DEF_COL, alpha=0.25, hatch="//", edgecolor=DEF_COL,
                             label=f"Default's own gain (+{d[-1]:.1f} PgC):\na static baseline would also credit this")],
              loc="upper left", fontsize=15, frameon=False, handlelength=2.2, handleheight=1.4)
    # right: definition and accounting points
    X = 0.585
    fig.text(X, 0.80, r"$\mathrm{OP}(t)=\sum_{2024}^{t}\,(\mathrm{NBP}_{\mathrm{management}}-\mathrm{NBP}_{\mathrm{counterfactual}})$",
             fontsize=19, color=INK, va="center")
    fig.text(X, 0.735, "RF − Default,  RH − Default,  Default − DF", fontsize=16, color=INK2, va="center")
    pts = [("NBP is the full net carbon exchange:", "photosynthesis, respiration, fire, land-use\nconversion and harvest (via wood products)"),
           ("Summed over the region", "each 4 km cell weighted by its land area;\naccumulated from 2024"),
           ("Same as the difference in total ecosystem", "carbon (wood products included) between runs"),
           ("Positive = more carbon stored on land", "than in the counterfactual"),
           ("The counterfactual is dynamic:", "it follows the same SSP climate, CO₂ and land use")]
    y = 0.665
    for head, body in pts:
        fig.text(X, y, "•", fontsize=18, color=INK, va="top")
        fig.text(X + 0.018, y, head, fontsize=16.5, color=INK, fontweight="bold", va="top")
        fig.text(X + 0.018, y - 0.036, body, fontsize=15.5, color=INK, va="top", linespacing=1.3)
        y -= 0.105
    fig.text(X, 0.135, "A static 2024 baseline would over-credit RF by:", fontsize=16, color=INK, fontweight="bold", va="center")
    fig.text(X, 0.07, "\n".join("     ".join(f"{s} +{over[s][2]:.0f} %" for s in SSPS[k:k + 2]) for k in (0, 2)), fontsize=16,
             color=INK, va="center", linespacing=1.4)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "offset_potential_method.png")
    fig.savefig(p, dpi=200, facecolor="white")
    plt.close(fig)
    for s in SSPS:
        print(f"{s}: RF - Default {over[s][0]:+.2f} PgC, Default cumulative NBP {over[s][1]:+.2f} PgC, static over-credit {over[s][2]:+.0f}%")
    print("wrote", p)


if __name__ == "__main__":
    main()
