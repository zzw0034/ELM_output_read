"""
Legacy asset fig03: standing stocks and management-induced pool differences.

Feeds new Main Figure 4 / Results 3.3. Panel A sums six pool groups for
Default/RF/DF/RH at 2024 and 2091-2100; 2024 is already an intervention year.
Panel B uses managed-Default for all runs, so DF has the opposite sign from
the Default-DF avoided-loss convention used in the printed benefit table.

Standing-stock shares are not management-benefit shares. The provisional
66-70% aboveground increment shares are based on selected-pool sums, not a
closed partition of native TOTECOSYSC. The unresolved residual must be traced
in the actual model version; its magnitude need not be small in every year.
Roots, CWD, litter and SOC are outside-AGB pools; not all are belowground.

RF includes restoration/protection and broad zero harvest. Interpretation
and new figure numbering follow MANUSCRIPT_BLUEPRINT.md and FIGURE_PLAN.md.

Usage inside an approved Slurm allocation:
    python fig03_carbon_pool_partitioning.py [0.5deg|4km]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import (HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, POOL_COMPONENTS,
                    OUTDIR, load_annual_series, save_cache, load_cache, cache_exists)

SCENARIOS = ["SSP3-7.0", "SSP3-7.0 RF", "SSP3-7.0 DF", "SSP3-7.0 RH"]
SHORT = {"SSP3-7.0": "Default", "SSP3-7.0 RF": "RF", "SSP3-7.0 DF": "DF", "SSP3-7.0 RH": "RH"}
POOL_VARS = [v for v, _ in POOL_COMPONENTS]
# Aggregate the nine component pools into the three groups the proposal names,
# so the figure answers its question directly rather than showing nine slivers.
GROUPS = [
    ("Aboveground wood", ["LIVESTEMC", "DEADSTEMC"], "tab:brown"),
    ("Leaf", ["LEAFC"], "tab:green"),
    ("Roots", ["FROOTC", "LIVECROOTC", "DEADCROOTC"], "olive"),
    ("Coarse woody debris", ["CWDC"], "tan"),
    ("Litter", ["TOTLITC"], "goldenrod"),
    ("Soil organic carbon", ["TOTSOMC"], "dimgray"),
]


def get_series(label, case, subdir, res):
    key = f"{res}__{case}__pools"
    if cache_exists(key):
        print(f"  cache hit: {label}")
        return load_cache(key)
    print(f"  loading {label} ({case}) ...")
    s = load_annual_series(case, POOL_VARS, subdir=subdir)
    save_cache(s, key)
    return s


def group_totals(series, year_mask):
    """PgC per pool group, averaged over the selected years."""
    return {g: float(np.nanmean(sum(series[v + "_PgC"] for v in vs)[year_mask]))
            for g, vs, _ in GROUPS}


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else "0.5deg"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)
    os.makedirs(OUTDIR, exist_ok=True)

    series = {s: get_series(s, cases[s], subdir, res) for s in SCENARIOS}
    year = series[SCENARIOS[0]]["year"]
    for s in SCENARIOS[1:]:
        assert np.array_equal(series[s]["year"], year), \
            f"{s} year axis differs from {SCENARIOS[0]} -- cannot align stock comparisons"
    start = year == 2024
    end = year >= 2091

    totals = {s: {"2024": group_totals(series[s], start),
                  "2091-2100": group_totals(series[s], end)} for s in SCENARIOS}

    # Panel A: stacked pools, each scenario at both periods.
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    ax = axes[0]
    labels, xpos = [], []
    x = 0
    for s in SCENARIOS:
        for period in ["2024", "2091-2100"]:
            bottom = 0.0
            for gname, _, color in GROUPS:
                val = totals[s][period][gname]
                ax.bar(x, val, bottom=bottom, color=color, width=0.75,
                       edgecolor="white", linewidth=0.4,
                       label=gname if (x == 0) else None)
                bottom += val
            labels.append(f"{SHORT[s]}\n{period}")
            xpos.append(x)
            x += 1
        x += 0.5
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Selected-pool carbon sum (PgC)")
    ax.set_title("Carbon partitioning by pool", fontsize=11)
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=8, ncol=2)

    # Panel B: change in each pool relative to Default at end of century --
    # i.e. which pools each practice actually moves.
    ax = axes[1]
    width = 0.25
    gnames = [g for g, _, _ in GROUPS]
    xs = np.arange(len(gnames))
    for i, s in enumerate(["SSP3-7.0 RF", "SSP3-7.0 DF", "SSP3-7.0 RH"]):
        deltas = [totals[s]["2091-2100"][g] - totals["SSP3-7.0"]["2091-2100"][g]
                  for g in gnames]
        ax.bar(xs + i * width, deltas, width=width, label=f"{SHORT[s]} - Default")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(xs + width)
    ax.set_xticklabels(gnames, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Change vs Default, 2091-2100 (PgC)")
    ax.set_title("Which pools each practice moves\n(note: DF shown as DF-Default, i.e. "
                 "the negative of the Table 2 offset)", fontsize=10)
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=8)

    fig.suptitle(f"SEUS {res} SSP3-7.0: carbon pool partitioning and management effects",
                 fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, f"fig03_carbon_pool_partitioning_{res}.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)

    print(f"\n--- Pool partitioning, 2091-2100 mean (PgC) ---")
    header = f"{'pool':24s}" + "".join(f"{SHORT[s]:>12s}" for s in SCENARIOS)
    print(header)
    for g in gnames:
        row = f"{g:24s}" + "".join(f"{totals[s]['2091-2100'][g]:12.3f}" for s in SCENARIOS)
        print(row)
    print(f"{'TOTAL (6 groups)':24s}" +
          "".join(f"{sum(totals[s]['2091-2100'].values()):12.3f}" for s in SCENARIOS))

    # Stock-composition number (context only -- NOT the management-benefit number).
    d = totals["SSP3-7.0"]["2091-2100"]
    agb_stock = d["Aboveground wood"] + d["Leaf"]
    outside_agb_stock = d["Roots"] + d["Litter"] + d["Soil organic carbon"] + d["Coarse woody debris"]
    print(f"\n[STOCK composition, Default 2091-2100 -- NOT a management-benefit number]")
    print(f"  aboveground biomass (wood+leaf) = {agb_stock:.2f} PgC "
          f"({100*agb_stock/(agb_stock+outside_agb_stock):.1f}% of the 6-group stock)")
    print(f"  outside-AGB pools (roots+litter+CWD+soil) = {outside_agb_stock:.2f} PgC "
          f"({100*outside_agb_stock/(agb_stock+outside_agb_stock):.1f}%)")
    print("  This describes the selected standing-stock pools, not management benefits.")
    print("  A large SOC stock does not establish the size of its management response.")

    # The number that actually answers "how much of the MANAGEMENT BENEFIT is
    # outside AGB": increment (managed - Default), not stock composition.
    print(f"\n[INCREMENT attributable to management, 2091-2100 -- the correct comparison]")
    print(f"{'practice':10s} {'B_total':>9} {'B_AGB':>9} {'B_outsideAGB':>13} {'AGB share':>10}")
    default_end = totals["SSP3-7.0"]["2091-2100"]
    for s, sign in [("SSP3-7.0 RF", +1), ("SSP3-7.0 RH", +1), ("SSP3-7.0 DF", -1)]:
        managed_end = totals[s]["2091-2100"]
        # sign=-1 for DF applies proposal Table 2's convention (Default - DF).
        b_total = sign * sum(managed_end[g] - default_end[g] for g in gnames)
        b_agb = sign * ((managed_end["Aboveground wood"] - default_end["Aboveground wood"]) +
                        (managed_end["Leaf"] - default_end["Leaf"]))
        b_outside = b_total - b_agb
        share = 100 * b_agb / b_total if b_total != 0 else float("nan")
        print(f"{SHORT[s]:10s} {b_total:9.3f} {b_agb:9.3f} {b_outside:13.3f} {share:9.1f}%")
    print("  (RF/RH: managed - Default. DF: Default - DF, per proposal Table 2's sign convention.)")
    print("  NOTE: these B_total values are 6-group sums, not the native-TOTECOSYSC offsets in")
    print("  fig01 -- the discrepancy is unresolved; see the closure caveat in the docstring.")

    print(f"\nFigure written to {out}")


if __name__ == "__main__":
    main()
