"""
Figure 2, per-scenario panels, version with ABSOLUTE forest-area change (ELM 4 km, results only).

Same layout as plot_scenario_management_benefits.py, one figure per SSP, 2024-2100:
  (a) cumulative NBP benefit since 2024: RF - Default, RH - Default   [PgC]        (unchanged)
  (b) cumulative NBP benefit since 2024: Default - DF (38000 s pair)  [PgC]        (unchanged)
  (c) forest (tree-PFT) area change since 2023 of each RUN: RF and the 36000 s Default [10^3 km2]
  (d) forest area change since 2023 of each RUN: DF and the 38000 s Default         [10^3 km2]

Why (c) and (d) differ from the paired-difference version: RF - Default subtracts the Default's own
forest trend, so after 2050 (when the RF area is fixed at its plateau while the Default keeps growing)
it looks as if the RF forest shrinks. The absolute change of each run shows what actually happens.
RH leaves forest area identical to its Default (difference exactly 0 in every year), so it has no
separate line in (c). DF holds zero forest from 2024, so its change is -(2023 forest area).

Inputs: `_cache/figure2/transient_forest_area_4km.npz` (2023 forest area) and
`_cache/figure2/future_4km/<SSP>[_RF|_RH|_cds38000|_DF_cds38000]__{totals,forest}.npz`.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \\
        code/figure2/plot_scenario_management_forest_abs.py [SSP3-7.0 ...]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import (CACHE, COLORS, INK, INK2, OUT_DIR, SSPS, benefits, curve, style)  # noqa: E402

DEFAULT_GREY = "#6f6e69"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def forest(key):
    f = np.load(os.path.join(CACHE, f"{key}__forest.npz"))
    return f["year"], f["tree_area_km2"] / 1e3


def line(ax, year, y, color, label, ls="-", lw=2.8, text=None):
    ax.plot(year, y, color=color, lw=lw, ls=ls, solid_capstyle="round", zorder=3)
    ax.plot([year[-1]], [y[-1]], "o", color=color, ms=6, mec="white", mew=1.4, zorder=4)
    ax.annotate(text or f"{label} {y[-1]:+.0f}".replace("-", "−"), xy=(year[-1], y[-1]), xytext=(6, 0), textcoords="offset points", fontsize=11.5,
                color=INK, va="center", fontweight="semibold", annotation_clip=False)


def main():
    todo = sys.argv[1:] or SSPS
    ref = float(np.load(os.path.join(ROOT, "_cache/figure2/transient_forest_area_4km.npz"))["tree_area_km2"][-1] / 1e3)
    os.makedirs(OUT_DIR, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    print(f"2023 forest area {ref:.1f} x10^3 km2 (reference)")
    print(f"{'SSP':9s} {'Def36 2100':>11s} {'RF 2050':>9s} {'RF 2100':>9s} {'Def38 2100':>11s} {'DF':>9s}   change since 2023, 10^3 km2")
    for ssp in todo:
        year, b = benefits(ssp)
        runs = {k: forest(f"{ssp}{s}") for k, s in {"Def36": "", "RF": "_RF", "RH": "_RH", "Def38": "_cds38000", "DF": "_DF_cds38000"}.items()}
        chg = {k: v[1] - ref for k, v in runs.items()}
        assert np.allclose(runs["RH"][1], runs["Def36"][1]), f"{ssp}: RH forest area differs from the Default"
        i50 = int(np.where(year == 2050)[0][0])
        print(f"{ssp:9s} {chg['Def36'][-1]:+11.1f} {chg['RF'][i50]:+9.1f} {chg['RF'][-1]:+9.1f} {chg['Def38'][-1]:+11.1f} {chg['DF'][-1]:+9.1f}")

        fig, axes = plt.subplots(2, 2, figsize=(14.5, 9.0), sharex=True)
        fmt_c = lambda v: f"{v:+.2f} PgC"
        for mg in ("RF", "RH"):
            curve(axes[0, 0], year, b[mg][0], mg, fmt_c)
        curve(axes[0, 1], year, b["DF"][0], "DF", fmt_c)
        line(axes[1, 0], year, chg["RF"], COLORS["RF"], "RF")
        line(axes[1, 0], year, chg["Def36"], DEFAULT_GREY, "Default", ls=(0, (5, 2)))
        line(axes[1, 1], year, chg["Def38"], DEFAULT_GREY, "Default", ls=(0, (5, 2)))
        line(axes[1, 1], year, chg["DF"], COLORS["DF"], "DF", text="DF: no forest")
        titles = {(0, 0): "(a) Cumulative NBP benefit: RF − Default, RH − Default",
                  (0, 1): "(b) Cumulative NBP benefit: Default − DF (avoided loss)",
                  (1, 0): "(c) Forest area change since 2023: RF and Default (RH = Default)",
                  (1, 1): "(d) Forest area change since 2023: DF and Default"}
        ylabs = {0: "PgC", 1: "10$^3$ km$^2$"}
        for (r, c), ax in np.ndenumerate(axes):
            ax.set_title(titles[(r, c)], loc="left", fontsize=13, fontweight="semibold", pad=10)
            style(ax, ylabs[r])
            ax.set_xlim(year[0] - 2, year[-1] + 2)
        for ax in axes[1]:
            ax.set_xlabel("year", color=INK, fontsize=12)
        fig.suptitle(f"{ssp}: management benefits of the ELM 4 km runs, 2024–{year[-1]} (forest area shown as absolute change)",
                     x=0.045, y=0.995, ha="left", fontsize=16, fontweight="semibold")
        fig.text(0.045, 0.005,
                 "(a), (b): RF and RH paired with the 36000 s Default, DF with the 38000 s Default; positive = more carbon than the counterfactual.\n"
                 f"(c), (d): each run's own forest (tree-PFT) area minus its 2023 value ({ref:.0f} ×10³ km²). RF is ramped up linearly until 2050 and then held "
                 "fixed, so\nits forest area is flat afterwards while the Default keeps changing. DF holds no forest from 2024 and is an idealized avoided-loss bound.",
                 fontsize=9.5, color=INK2, va="bottom", linespacing=1.5)
        fig.tight_layout(rect=(0, 0.07, 0.985, 0.965), h_pad=2.2, w_pad=4.0)
        out = os.path.join(OUT_DIR, f"management_benefits_forest_abs_{ssp}_4km.png")
        fig.savefig(out, dpi=200, facecolor="white")
        plt.close(fig)
        print(f"Saved {out}")


if __name__ == "__main__":
    main()
