"""
Figure 2, per-scenario panels: paired management benefits of the ELM 4 km future
runs (results only, 4 km only), one figure per SSP, 2024-2100:

  row 1  cumulative NBP benefit since 2024                 [PgC]
  row 2  forest (tree-PFT) area change                     [10^3 km2]
  left column   restoration/protection (RF - Default) and reduced harvest
                (RH - Default), both against the crit_dayl_stress = 36000 s Default
  right column  avoided-loss upper bound (Default - DF), against the 38000 s
                `cds38000` Default (blueprint A2: DF is paired with the 38000 s
                Default); its own y axes, since DF is ~10x larger and paired differently

Sign convention (blueprint D4): every curve is positive when the management run holds
more carbon / more forest than its counterfactual. DF is "Default - DF", the carbon or
forest area that is avoided being lost, an idealized bound, not a policy estimate.
Cumulative NBP benefit(t) = sum_{y=2024..t} (NBP_management - NBP_Default)(y) for RF and
RH, and (NBP_Default - NBP_DF)(y) for DF; forest area is the same-sign annual difference.
NBP is positive for a sink and includes fire, land use and harvest.

Inputs (pulled from Pathfinder `_cache/figure2/future_4km/` into the local one), made
by extract_domain_totals.py and extract_forest_area.py: <SSP>[ _RF| _RH| _cds38000|
_DF_cds38000]__{totals,forest}.npz.

Colours: categorical slots 1-3 of the dataviz reference palette (blue RF, orange RH,
aqua DF), each curve directly labelled at its end; black axes; one y axis per panel.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \\
        code/figure2/plot_scenario_management_benefits.py [SSP3-7.0 ...]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root
CACHE = os.path.join(ROOT, "_cache/figure2/future_4km")
OUT_DIR = os.path.join(ROOT, "figures/figure2")
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e9e8e4"
COLORS = {"RF": "#2a78d6", "RH": "#eb6834", "DF": "#1baf7a"}
LABELS = {"RF": "RF  restoration/protection", "RH": "RH  reduced harvest", "DF": "DF  avoided loss"}


def load(key):
    t = np.load(os.path.join(CACHE, f"{key}__totals.npz"))
    f = np.load(os.path.join(CACHE, f"{key}__forest.npz"))
    assert np.array_equal(t["year"], f["year"]), f"{key}: h0 and h1 years differ"
    return t["year"], t["NBP"], f["tree_area_km2"] / 1e3, t["TOTECOSYSC"]


def benefits(ssp):
    """Paired benefit curves for one SSP: {mgmt: (cum NBP benefit, forest area benefit, d stock benefit)}."""
    runs = {k: load(f"{ssp}{s}") for k, s in
            {"Def36": "", "RF": "_RF", "RH": "_RH", "Def38": "_cds38000", "DF": "_DF_cds38000"}.items()}
    year = runs["Def36"][0]
    for k, v in runs.items():
        assert np.array_equal(v[0], year), f"{ssp} {k}: year axis differs"
    out = {}
    for mg, (pos, neg) in {"RF": ("RF", "Def36"), "RH": ("RH", "Def36"), "DF": ("Def38", "DF")}.items():
        dn = runs[pos][1] - runs[neg][1]            # NBP difference, PgC/yr
        out[mg] = (np.cumsum(dn), runs[pos][2] - runs[neg][2], runs[pos][3] - runs[neg][3])
    return year, out


def style(ax, ylabel):
    ax.set_ylabel(ylabel, color=INK, fontsize=12)
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


def curve(ax, year, y, mg, fmt):
    ax.plot(year, y, color=COLORS[mg], lw=2.6, solid_capstyle="round", zorder=3)
    ax.plot([year[-1]], [y[-1]], "o", color=COLORS[mg], ms=6, mec="white", mew=1.4, zorder=4)
    ax.annotate(f"{LABELS[mg].split()[0]} {fmt(y[-1])}" + ("  (no change)" if np.all(y == 0) else ""), xy=(year[-1], y[-1]), xytext=(6, 0), textcoords="offset points",
                fontsize=11.5, color=INK, va="center", fontweight="semibold", annotation_clip=False)


def main():
    todo = sys.argv[1:] or SSPS
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"{'SSP':9s} {'mgmt':4s} {'cumNBP2050':>11s} {'cumNBP2100':>11s} {'forest2050':>11s} {'forest2100':>11s} "
          f"{'dStock2100':>11s}   (PgC; 10^3 km2; stock = TOTECOSYSC difference)")
    for ssp in todo:
        year, b = benefits(ssp)
        i50 = int(np.where(year == 2050)[0][0])
        for mg, (cum, fa, ds) in b.items():
            print(f"{ssp:9s} {mg:4s} {cum[i50]:+11.3f} {cum[-1]:+11.3f} {fa[i50]:+11.1f} {fa[-1]:+11.1f} {ds[-1]:+11.3f}")
        plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
        fig, axes = plt.subplots(2, 2, figsize=(14.5, 9.0), sharex=True)
        fmt_c = lambda v: f"{v:+.2f} PgC"
        fmt_a = lambda v: f"{v:+.1f}"
        for mg in ("RF", "RH"):
            curve(axes[0, 0], year, b[mg][0], mg, fmt_c)
            curve(axes[1, 0], year, b[mg][1], mg, fmt_a)
        curve(axes[0, 1], year, b["DF"][0], "DF", fmt_c)
        curve(axes[1, 1], year, b["DF"][1], "DF", fmt_a)
        titles = {(0, 0): "(a) Cumulative NBP benefit: RF − Default, RH − Default",
                  (0, 1): "(b) Cumulative NBP benefit: Default − DF (avoided loss)",
                  (1, 0): "(c) Forest area change: RF − Default, RH − Default",
                  (1, 1): "(d) Forest area change: Default − DF (avoided loss)"}
        ylabs = {0: "PgC", 1: "10$^3$ km$^2$"}
        for (r, c), ax in np.ndenumerate(axes):
            ax.set_title(titles[(r, c)], loc="left", fontsize=13, fontweight="semibold", pad=10)
            style(ax, ylabs[r])
            ax.set_xlim(year[0] - 2, year[-1] + 2)
        for ax in axes[1]:
            ax.set_xlabel("year", color=INK, fontsize=12)
        fig.suptitle(f"{ssp}: management benefits of the ELM 4 km runs, 2024–{year[-1]}", x=0.045, y=0.995, ha="left",
                     fontsize=16, fontweight="semibold")
        fig.text(0.045, 0.005,
                 "RF and RH are paired with the 36000 s Default, DF with the 38000 s Default (the same crit_dayl_stress in every pair). "
                 "Positive = the management run holds more carbon or forest than its counterfactual.\n"
                 "Management acts from the first simulated year, so the 2024 differences are not zero (DF replaces nearly all forest in 2024; "
                 "RF adds forest gradually). DF is an idealized avoided-loss bound.",
                 fontsize=9.5, color=INK2, va="bottom", linespacing=1.5)
        fig.tight_layout(rect=(0, 0.055, 0.985, 0.965), h_pad=2.2, w_pad=4.0)
        out = os.path.join(OUT_DIR, f"management_benefits_{ssp}_4km.png")
        fig.savefig(out, dpi=200, facecolor="white")
        plt.close(fig)
        print(f"Saved {out}")


if __name__ == "__main__":
    main()
