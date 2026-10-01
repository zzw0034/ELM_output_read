"""
Figure 2, two-panel version of two existing single-panel figures (the originals are kept):

  (a) forest (tree-PFT) area change since 2023, four SSPs   (= ssp_forest_area_change_2000-2100_4km.png)
  (b) cumulative NBP since 2010, four SSPs                  (= ssp_nbp_cumulative_2010-2100_4km.png)

ELM 4 km, 36000 s Default runs; history 2000-2023 (grey) from the 4 km transient, projections 2024-2100
from the four Default future runs. NBP is positive for a sink and includes fire, land use and harvest.
Panel (b) accumulates the annual regional NBP from 2010; the projections continue from the 2023 value.
Data, loading and colours are those of plot_default_ssp_trajectories.py (notes sections 3.5 to 3.7).

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure2/plot_default_ssp_forest_and_cumnbp.py [cumulative_start]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_default_ssp_trajectories import COLORS, HIST_DARK, INK, INK2, OUT_DIR, SSPS, load, style  # noqa: E402

HIST_START = 2000


def label_end(ax, x, y, text, color, ypos=None):
    ax.plot([x], [y], "o", color=color, ms=6.5, mec="white", mew=1.4, zorder=5)
    ax.annotate(text, xy=(x, y), xytext=(x + 3, y if ypos is None else ypos), textcoords="data", fontsize=11.5, color=INK,
                va="center", fontweight="semibold", annotation_clip=False,
                arrowprops=dict(arrowstyle="-", color="#b9b8b3", lw=0.8, shrinkA=0, shrinkB=3) if ypos is not None else None)


def nudge(values, gap):
    """Label y positions: keep each value, push labels apart when closer than `gap` (values: dict key -> y)."""
    pos = {}
    for k in sorted(values, key=values.get):
        pos[k] = values[k] if not pos else max(values[k], max(pos.values()) + gap)
    return pos


def main():
    cstart = int(sys.argv[1]) if len(sys.argv) > 1 else 2010
    hist, fut = load(HIST_START)
    assert cstart >= hist["year"][0]
    ref = hist["forest"][-1]  # 2023 forest area
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(19, 6.6))

    # ---- (a) forest area change since 2023
    ax1.plot(hist["year"], hist["forest"] - ref, color=HIST_DARK, lw=3.0, solid_capstyle="round", zorder=3)
    ends = {}
    for ssp in SSPS:
        d = fut[ssp]
        yr = np.concatenate([[hist["year"][-1]], d["year"]])
        ch = np.concatenate([[0.0], d["forest"] - ref])
        ends[ssp] = ch[-1]
        ax1.plot(yr, ch, color=COLORS[ssp], lw=3.0, solid_capstyle="round", zorder=4)
    ax1.axhline(0, color="black", lw=0.9, zorder=2)
    ax1.axvline(hist["year"][-1] + 0.5, color=HIST_DARK, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax1.set_xlim(HIST_START - 2, 2137)
    ax1.set_xticks(range(HIST_START, 2101, 20))
    style(ax1, "forest area change since 2023  (10$^3$ km$^2$)")
    ax1.set_xlabel("year", color=INK, fontsize=12)
    ax1.set_title("(a) Forest (tree-PFT) area change since 2023", loc="left", fontsize=14, fontweight="semibold", pad=12)
    pos = nudge(ends, 0.06 * (ax1.get_ylim()[1] - ax1.get_ylim()[0]))
    for ssp in SSPS:
        label_end(ax1, 2100, ends[ssp], f"{ssp}  " + f"{ends[ssp]:+.0f}".replace("-", "−"), COLORS[ssp], pos[ssp] if abs(pos[ssp] - ends[ssp]) > 1e-9 else None)

    # ---- (b) cumulative NBP since cstart
    hm = hist["year"] >= cstart
    hyr, chist = hist["year"][hm], np.cumsum(hist["NBP"][hm])
    ax2.plot(hyr, chist, color=HIST_DARK, lw=3.0, solid_capstyle="round", zorder=3)
    ends2 = {}
    for ssp in SSPS:
        d = fut[ssp]
        yr = np.concatenate([[hyr[-1]], d["year"]])
        cum = np.concatenate([[chist[-1]], chist[-1] + np.cumsum(d["NBP"])])
        ends2[ssp] = cum[-1]
        ax2.plot(yr, cum, color=COLORS[ssp], lw=3.0, solid_capstyle="round", zorder=4)
    ax2.axhline(0, color="black", lw=0.9, zorder=2)
    ax2.axvline(hyr[-1] + 0.5, color=HIST_DARK, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax2.set_xlim(cstart - 2, 2137)
    ax2.set_xticks([t for t in range(2020, 2101, 20)])
    style(ax2, f"cumulative NBP since {cstart}  (PgC)")
    ax2.set_xlabel("year", color=INK, fontsize=12)
    ax2.set_title(f"(b) Cumulative regional NBP since {cstart} (positive = sink)", loc="left", fontsize=14, fontweight="semibold", pad=12)
    pos2 = nudge(ends2, 0.06 * (ax2.get_ylim()[1] - ax2.get_ylim()[0]))
    for ssp in SSPS:
        label_end(ax2, 2100, ends2[ssp], f"{ssp}  {ends2[ssp]:+.1f}", COLORS[ssp], pos2[ssp] if abs(pos2[ssp] - ends2[ssp]) > 1e-9 else None)

    fig.legend(handles=[Line2D([0], [0], color=HIST_DARK, lw=3, label="historical")] +
                       [Line2D([0], [0], color=COLORS[s], lw=3, label=s) for s in SSPS],
               loc="upper left", ncol=5, frameon=False, fontsize=12, labelcolor=INK2, bbox_to_anchor=(0.03, 0.935), columnspacing=2.2)
    fig.suptitle("Default runs of the four SSPs, ELM 4 km", x=0.04, y=0.995, ha="left", fontsize=17, fontweight="semibold")
    fig.text(0.04, 0.003, f"Forest area: tree-PFT area minus its 2023 value ({ref:.0f} ×10³ km²). NBP: annual regional NBP summed from {cstart}; the 2024–2100 "
             f"projections continue from the 2023 value ({chist[-1]:+.2f} PgC).\nSSP runs use crit_dayl_stress = 36000 s. NBP includes fire, land use and harvest.",
             fontsize=10, color=INK2, va="bottom", linespacing=1.5)
    fig.tight_layout(rect=(0, 0.06, 1, 0.89), w_pad=3.0)
    out = os.path.join(OUT_DIR, f"ssp_forest_and_cumulative_nbp_{cstart}-2100_4km.png")
    fig.savefig(out, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    print(f"2100 forest change (10^3 km2): " + ", ".join(f"{s} {ends[s]:+.1f}" for s in SSPS))
    print(f"2100 cumulative NBP since {cstart} (PgC): " + ", ".join(f"{s} {ends2[s]:+.2f}" for s in SSPS))


if __name__ == "__main__":
    main()
