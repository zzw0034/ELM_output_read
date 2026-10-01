"""
Forest (tree-PFT) area change under the four SSPs and the three management measures, ELM 4 km
(results only): one column per SSP, 2024-2100, change relative to the 2023 forest area.

  row 1  RF (blue), RH (orange) and the 36000 s Default (grey)
  row 2  DF (aqua) and the 38000 s Default (grey), own axes because DF holds no forest

RH changes the harvest rate but not the forest area: its curve is identical to its Default in every
year and SSP (asserted), so it is drawn as an orange dashed line on top of the grey Default line.
RF is the same forest in all four SSPs (one shared land-use file: +5.47 x10^3 km2 per year for 26
years, then fixed). The two Defaults have the same forest area (asserted): crit_dayl_stress does not
change land cover. DF has no forest from 2024, i.e. -(2023 forest area).

Inputs: `_cache/figure2/transient_forest_area_4km.npz` (2023 forest area) and
`_cache/figure2/future_4km/<SSP>[_RF|_RH|_cds38000|_DF_cds38000]__forest.npz`
(extract_forest_area.py, notes section 3.6).

Colours: categorical slots of the dataviz reference palette as in the other Figure 2 plots (blue RF,
orange RH, aqua DF), grey for the Default; black axes; one y axis per panel row.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure2/plot_forest_area_by_ssp_management.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import COLORS, GRID, INK, INK2, OUT_DIR, SSPS  # noqa: E402
from plot_scenario_management_forest_abs import ROOT, forest  # noqa: E402

DEFAULT_GREY = "#6f6e69"


def style(ax, ylabel=None):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=12.5)
    ax.grid(axis="y", color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.1)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=11, length=4, width=1.0)
    ax.axhline(0, color="black", lw=0.9, zorder=1)
    ax.margins(y=0.08)


def end(ax, year, y, text, color_dot):
    ax.plot([year[-1]], [y[-1]], "o", color=color_dot, ms=6, mec="white", mew=1.4, zorder=5)
    ax.annotate(text, xy=(year[-1], y[-1]), xytext=(6, 0), textcoords="offset points", fontsize=11, color=INK, va="center",
                fontweight="semibold", annotation_clip=False)


def main():
    ref = float(np.load(os.path.join(ROOT, "_cache/figure2/transient_forest_area_4km.npz"))["tree_area_km2"][-1] / 1e3)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    os.makedirs(OUT_DIR, exist_ok=True)
    fig, axes = plt.subplots(2, 4, figsize=(18, 8.6), sharex=True, sharey="row")
    print(f"2023 forest area {ref:.1f} x10^3 km2")
    print(f"{'SSP':9s} {'Default 2050':>13s} {'Default 2100':>13s} {'RF':>8s} {'RH':>6s} {'DF':>8s}   (change since 2023, 10^3 km2)")
    for col, ssp in enumerate(SSPS):
        runs = {k: forest(f"{ssp}{s}") for k, s in {"Def36": "", "RF": "_RF", "RH": "_RH", "Def38": "_cds38000", "DF": "_DF_cds38000"}.items()}
        year = runs["Def36"][0]
        chg = {k: v[1] - ref for k, v in runs.items()}
        assert np.allclose(runs["RH"][1], runs["Def36"][1]), f"{ssp}: RH forest area differs from its Default"
        assert np.allclose(runs["Def38"][1], runs["Def36"][1]), f"{ssp}: the two Defaults differ in forest area"
        i50 = int(np.where(year == 2050)[0][0])
        print(f"{ssp:9s} {chg['Def36'][i50]:+13.1f} {chg['Def36'][-1]:+13.1f} {chg['RF'][-1]:+8.1f} {chg['RH'][-1]:+6.1f} {chg['DF'][-1]:+8.1f}")

        top, bot = axes[0, col], axes[1, col]
        top.plot(year, chg["Def36"], color=DEFAULT_GREY, lw=3.4, solid_capstyle="round", zorder=3)
        top.plot(year, chg["RH"], color=COLORS["RH"], lw=2.0, ls=(0, (4, 3)), zorder=4)
        top.plot(year, chg["RF"], color=COLORS["RF"], lw=3.0, solid_capstyle="round", zorder=3)
        end(top, year, chg["RF"], f"RF {chg['RF'][-1]:+.0f}", COLORS["RF"])
        end(top, year, chg["Def36"], f"Default, RH {chg['Def36'][-1]:+.0f}".replace("-", "−"), DEFAULT_GREY)
        top.set_title(ssp, loc="left", fontsize=15, fontweight="semibold", pad=10)

        bot.plot(year, chg["Def38"], color=DEFAULT_GREY, lw=3.4, solid_capstyle="round", zorder=3)
        bot.plot(year, chg["DF"], color=COLORS["DF"], lw=3.0, solid_capstyle="round", zorder=4)
        end(bot, year, chg["DF"], "DF: no forest", COLORS["DF"])
        end(bot, year, chg["Def38"], f"Default {chg['Def38'][-1]:+.0f}".replace("-", "−"), DEFAULT_GREY)

        for ax in (top, bot):
            ax.set_xlim(2022, 2137)
            ax.set_xticks([2030, 2050, 2070, 2090])
            style(ax, None)
        bot.set_xlabel("year", color=INK, fontsize=12)
    axes[0, 0].set_ylabel("RF, RH and Default  (10$^3$ km$^2$)", color=INK, fontsize=12.5)
    axes[1, 0].set_ylabel("DF and Default  (10$^3$ km$^2$)", color=INK, fontsize=12.5)
    fig.legend(handles=[Line2D([0], [0], color=COLORS["RF"], lw=3, label="RF  restoration/protection"),
                        Line2D([0], [0], color=COLORS["RH"], lw=2, ls=(0, (4, 3)), label="RH  reduced harvest (= Default)"),
                        Line2D([0], [0], color=COLORS["DF"], lw=3, label="DF  no forest (upper bound)"),
                        Line2D([0], [0], color=DEFAULT_GREY, lw=3.4, label="Default")],
               loc="upper left", ncol=4, frameon=False, fontsize=12, labelcolor=INK2, bbox_to_anchor=(0.03, 0.955), columnspacing=2.2)
    fig.suptitle("Forest area change since 2023 under four SSPs and three management measures, ELM 4 km", x=0.04, y=0.995, ha="left",
                 fontsize=16, fontweight="semibold")
    fig.text(0.04, 0.003, f"Each run's own tree-PFT area minus its 2023 value ({ref:.0f} ×10³ km²). RF is the same in every SSP (+5.5 ×10³ km² per year for 26 years, then held "
             "fixed); RH changes harvest, not area, so it equals the Default; DF has no forest from 2024.", fontsize=10, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 0.91), h_pad=2.6, w_pad=1.2)
    out = os.path.join(OUT_DIR, "forest_area_change_by_ssp_management_4km.png")
    fig.savefig(out, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
