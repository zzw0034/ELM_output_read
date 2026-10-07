"""
Figure 2, presentation versions that put the four SSPs on one slide (ELM 4 km, results only):

  management_summary_2100_4km.png
      x = the four SSPs; values at 2100. Row 1 cumulative NBP benefit since 2024 (PgC), row 2
      forest (tree-PFT) area change (10^3 km2). Left column RF and RH (paired with the 36000 s
      Default), right column DF (paired with the 38000 s Default; own axes, because DF is ~10x larger).
  management_rf_rh_cumNBP_4ssp_4km.png
      one panel per SSP, cumulative NBP benefit curves of RF and RH on a shared axis.
  management_summary_carbon_2100_4km.png
      the carbon-only version of the 2100 summary: one panel, RF, RH and DF side by side for each SSP on one
      y axis (user request 2026-10-06; it used to be two panels, RF and RH | DF), no forest-area panel.

Sign convention (blueprint D4): RF - Default, RH - Default, Default - DF; positive = the management
run holds more carbon or forest than its counterfactual. DF is an idealized avoided-loss bound.
The benefit curves are built by plot_scenario_management_benefits.benefits() from the extracts in
`_cache/figure2/future_4km/` (see notes section 3.6).

Colours: categorical slots 1-3 of the dataviz reference palette (blue RF, orange RH, aqua DF); black axes.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure2/plot_management_summary_across_ssps.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_scenario_management_benefits import COLORS, GRID, INK, INK2, OUT_DIR, SSPS, benefits  # noqa: E402


def style(ax, ylabel=None, zero=True):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=13)
    ax.grid(axis="y", color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.2)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=12, length=4, width=1.1)
    if zero:
        ax.axhline(0, color="black", lw=1.0, zorder=1)
    ax.margins(y=0.12)


def bars(ax, data, mgmts, idx, fmt, ylabel):
    """Grouped bars: x = SSP, one bar per management in `mgmts`; data[ssp][mg] -> value."""
    n = len(mgmts)
    w = 0.7 / n
    for k, mg in enumerate(mgmts):
        x = np.arange(len(SSPS)) + (k - (n - 1) / 2) * w
        v = np.array([data[s][mg][idx] for s in SSPS])
        ax.bar(x, v, width=w * 0.92, color=COLORS[mg], zorder=3, lw=0)
        for xi, vi in zip(x, v):
            txt = fmt(vi) if abs(vi) > 1e-9 else "0"
            ax.annotate(txt, xy=(xi, vi), xytext=(0, 4 if vi >= 0 else -4), textcoords="offset points", ha="center",
                        va="bottom" if vi >= 0 else "top", fontsize=11.5, color=INK, fontweight="semibold")
    ax.set_xticks(np.arange(len(SSPS)))
    ax.set_xticklabels(SSPS)
    style(ax, ylabel)


def main():
    data = {}
    for ssp in SSPS:
        year, b = benefits(ssp)
        data[ssp] = {mg: (cum[-1], fa[-1], year, cum, fa) for mg, (cum, fa, _ds) in b.items()}
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    os.makedirs(OUT_DIR, exist_ok=True)

    # ---------------- summary at 2100
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 9.2), gridspec_kw={"width_ratios": [1.5, 1], "hspace": 0.32, "wspace": 0.18})
    fc = lambda v: f"{v:+.1f}"
    fa_ = lambda v: f"{v:+.0f}"
    bars(axes[0, 0], data, ("RF", "RH"), 0, fc, "PgC")
    bars(axes[0, 1], data, ("DF",), 0, fc, None)
    bars(axes[1, 0], data, ("RF", "RH"), 1, fa_, "10$^3$ km$^2$")
    bars(axes[1, 1], data, ("DF",), 1, fa_, None)
    titles = [["Cumulative NBP benefit: RF and RH", "Cumulative NBP benefit: DF (upper bound)"],
              ["Forest area change: RF and RH", "Forest area change: DF (upper bound)"]]
    for r in range(2):
        for c in range(2):
            axes[r, c].set_title(titles[r][c], loc="left", fontsize=14, fontweight="semibold", pad=10)
    # legend for the three managements, once
    from matplotlib.patches import Patch
    axes[0, 0].legend(handles=[Patch(color=COLORS["RF"], label="RF  restoration/protection"),
                               Patch(color=COLORS["RH"], label="RH  reduced harvest")],
                      frameon=False, loc="upper left", fontsize=11.5, labelcolor=INK2)
    fig.suptitle("Management benefits at 2100 under the four SSPs, ELM 4 km (2024–2100)", x=0.045, y=0.995, ha="left",
                 fontsize=17, fontweight="semibold")
    fig.text(0.045, 0.004, "RF − Default and RH − Default (36000 s Default); Default − DF (38000 s Default). Positive = more carbon or forest than "
             "the counterfactual.\nCumulative NBP summed from 2024. DF replaces nearly all forest in 2024, so about half of its benefit "
             "accrues in the first year; it is an idealized bound, not a policy estimate.", fontsize=10, color=INK2, va="bottom",
             linespacing=1.5)
    fig.tight_layout(rect=(0, 0.06, 1, 0.965))
    out1 = os.path.join(OUT_DIR, "management_summary_2100_4km.png")
    fig.savefig(out1, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)

    # ---------------- 1 x 4: RF and RH cumulative NBP benefit curves
    top = max(max(data[s][mg][3].max() for mg in ("RF", "RH")) for s in SSPS)
    fig, axes = plt.subplots(1, 4, figsize=(17, 5.4), sharey=True)
    for ax, ssp in zip(axes, SSPS):
        for mg in ("RF", "RH"):
            year, cum = data[ssp][mg][2], data[ssp][mg][3]
            ax.plot(year, cum, color=COLORS[mg], lw=3.0, solid_capstyle="round", zorder=3)
            ax.plot([year[-1]], [cum[-1]], "o", color=COLORS[mg], ms=7, mec="white", mew=1.5, zorder=4)
            ax.annotate(f"{cum[-1]:+.1f}", xy=(year[-1], cum[-1]), xytext=(7, 0), textcoords="offset points", fontsize=13,
                        color=INK, va="center", fontweight="semibold", annotation_clip=False)
        ax.set_title(ssp, loc="left", fontsize=15, fontweight="semibold", pad=10)
        ax.set_xlim(2022, 2112)
        ax.set_xticks([2030, 2050, 2070, 2090])
        ax.set_xlabel("year", color=INK, fontsize=12)
        style(ax, "cumulative NBP benefit since 2024  (PgC)" if ax is axes[0] else None)
        ax.set_ylim(-0.1, top * 1.08)
    axes[0].legend(handles=[Patch(color=COLORS["RF"], label="RF  restoration/protection"),
                            Patch(color=COLORS["RH"], label="RH  reduced harvest")],
                   frameon=False, loc="upper left", fontsize=12, labelcolor=INK2)
    fig.suptitle("Cumulative NBP benefit of forest restoration/protection (RF) and reduced harvest (RH), ELM 4 km",
                 x=0.04, y=1.0, ha="left", fontsize=17, fontweight="semibold")
    fig.text(0.04, -0.03, "RF − Default and RH − Default, both against the 36000 s Default; positive = more carbon stored than without the "
             "management. The DF upper bound (≈ +11 PgC) is on the summary figure.", fontsize=10.5, color=INK2, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.95), w_pad=2.0)
    out2 = os.path.join(OUT_DIR, "management_rf_rh_cumNBP_4ssp_4km.png")
    fig.savefig(out2, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out1}\nSaved {out2}")
    # ---------------- carbon only: one panel, RF, RH and DF side by side per SSP (user request 2026-10-06)
    fig, ax = plt.subplots(figsize=(13, 6.4))
    bars(ax, data, ("RF", "RH", "DF"), 0, fc, "cumulative NBP benefit since 2024  (PgC)")
    ax.set_ylim(0, max(data[s]["DF"][0] for s in SSPS) * 1.25)
    ax.legend(handles=[Patch(color=COLORS["RF"], label="RF  restoration/protection"),
                       Patch(color=COLORS["RH"], label="RH  reduced harvest"),
                       Patch(color=COLORS["DF"], label="DF  avoided loss (upper bound)")],
              frameon=False, loc="upper left", ncol=3, fontsize=12, labelcolor=INK2)
    fig.suptitle("Carbon benefit of forest management at 2100 under the four SSPs, ELM 4 km", x=0.045, y=1.0, ha="left",
                 fontsize=17, fontweight="semibold")
    fig.text(0.045, -0.02, "RF − Default and RH − Default (36000 s Default); Default − DF (38000 s Default). Positive = more carbon stored "
             "than the counterfactual, summed over 2024–2100.\nDF removes all forest (≈ 0.8 million km², 59 % of the region's land) in 2024 "
             "and keeps it removed: an idealized upper bound, about half of which accrues in the first year.",
             fontsize=10, color=INK2, va="top", linespacing=1.5)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    out3 = os.path.join(OUT_DIR, "management_summary_carbon_2100_4km.png")
    fig.savefig(out3, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out3}")
    print(f"{'SSP':9s}" + "".join(f"{mg + ' cumNBP':>14s}{mg + ' forest':>12s}" for mg in ("RF", "RH", "DF")))
    for s in SSPS:
        print(f"{s:9s}" + "".join(f"{data[s][mg][0]:+14.2f}{data[s][mg][1]:+12.1f}" for mg in ("RF", "RH", "DF")))


if __name__ == "__main__":
    main()
