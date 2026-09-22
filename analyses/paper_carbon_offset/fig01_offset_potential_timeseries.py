"""
Legacy asset fig01: management-induced ecosystem stock differences.

Feeds new Main Figure 2 / Results 3.2; see FIGURE_PLAN.md.
RF-Default is restoration/protection including broad zero harvest.
RH-Default is reduced prescribed harvest. Default-DF is an idealized
avoided-loss bound, not a deployable forest-preservation credit estimate.
Use native TOTECOSYSC separately from cumulative NBP and selected-pool sums.

The legacy cohort gives end-century benefits of roughly DF:RF:RH = 10:5:1.
Separate panels retain visibility of RH. These are version-specific results,
not observational validation or a completed pure-resolution experiment.

Usage inside an approved Slurm allocation:
    python fig01_offset_potential_timeseries.py [0.5deg|4km]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import (HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, OFFSET_DEFS,
                    OFFSET_COLORS, OUTDIR, load_annual_series, save_cache,
                    load_cache, cache_exists)

VARS = ["TOTECOSYSC", "TOTVEGC", "TOTSOMC"]


def get_series(label, case, subdir, res):
    key = f"{res}__{case}__ecosysc"
    if cache_exists(key):
        print(f"  cache hit: {label}")
        return load_cache(key)
    print(f"  loading {label} ({case}) ...")
    s = load_annual_series(case, VARS, subdir=subdir)
    save_cache(s, key)
    return s


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else "0.5deg"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)
    os.makedirs(OUTDIR, exist_ok=True)

    needed = sorted({c for pair in OFFSET_DEFS.values() for c in pair})
    series = {label: get_series(label, cases[label], subdir, res) for label in needed}

    year = series[needed[0]]["year"]
    for label in needed:
        assert np.array_equal(series[label]["year"], year), f"{label} year axis differs"

    offsets = {}
    for name, (pos, neg) in OFFSET_DEFS.items():
        offsets[name] = {
            v: series[pos][v + "_PgC"] - series[neg][v + "_PgC"]
            for v in VARS
        }

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, (name, d) in zip(axes, offsets.items()):
        c = OFFSET_COLORS[name]
        ax.plot(year, d["TOTECOSYSC"], color=c, lw=2, label="Total ecosystem C")
        ax.plot(year, d["TOTVEGC"], color=c, lw=1.2, ls="--", alpha=0.8, label="Vegetation C")
        ax.plot(year, d["TOTSOMC"], color=c, lw=1.2, ls=":", alpha=0.8, label="Soil organic C")
        ax.axhline(0, color="k", lw=0.6)
        ax.set_title(name, fontsize=10)
        ax.set_xlabel("year")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("Ecosystem carbon benefit (PgC)")

    fig.suptitle(
        f"SEUS {res} SSP3-7.0: ecosystem carbon benefits of management counterfactuals"
        f"\nRF includes restoration/protection; DF is an idealized avoided-loss bound",
        fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, f"fig01_offset_potential_timeseries_{res}.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)

    # Companion panel: RF and RH alone, on a shared axis they can actually be
    # read on (DF excluded).
    fig2, ax2 = plt.subplots(figsize=(8, 5.5))
    for name, d in offsets.items():
        if "Default - DF" in name:
            continue
        ax2.plot(year, d["TOTECOSYSC"], color=OFFSET_COLORS[name], lw=2,
                 label=name.replace("\n", " "))
    ax2.axhline(0, color="k", lw=0.6)
    ax2.set_xlabel("year")
    ax2.set_ylabel("Additional ecosystem carbon (PgC)")
    ax2.set_title(f"SEUS {res} SSP3-7.0: restoration/protection and reduced harvest\n"
                  "Stock differences relative to Default",
                  fontsize=10)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)
    fig2.tight_layout()
    out2 = os.path.join(OUTDIR, f"fig01b_offset_potential_RF_RH_{res}.png")
    fig2.savefig(out2, dpi=150)
    plt.close(fig2)

    print(f"\n--- Offset potential, total ecosystem C (PgC) ---")
    print(f"{'practice':40s} {'2050':>10} {'2100':>10} {'2091-2100':>12}")
    end = year >= 2091
    for name, d in offsets.items():
        i50 = int(np.where(year == 2050)[0][0])
        flat = name.replace("\n", " ")
        print(f"{flat:40s} {d['TOTECOSYSC'][i50]:10.3f} {d['TOTECOSYSC'][-1]:10.3f} "
              f"{np.nanmean(d['TOTECOSYSC'][end]):12.3f}")

    print(f"\nFigures written to {OUTDIR}")


if __name__ == "__main__":
    main()
