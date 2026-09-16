"""
Forest area (% of domain PFT-weighted area) over 1850-2023 (transient) and
2024-2100 (6 future scenarios), for the 0.5-deg SEUS dt3600 case family.

Forest = natpft 1..8 (FOREST_ITYPES in common.py), per HARVEST_SCENARIOS.md
convention. Plotted as a domain area-weighted % of total PFT weight (not an
absolute km^2 -- see HARVEST_SCENARIOS.md Sec.1's explicit warning that
%-of-cell PCT_NAT_PFT sums and true km^2 differ by ~5.8x and the conversion
factor is not constant; %-of-domain-weight here is internally consistent for
a *relative* time series but should not be read off as km^2).

Runs directly on Pathfinder. Figure written to OUTDIR_ROOT.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import TRANSIENT, FUTURE, FUTURE_STYLE, OUTDIR_ROOT, load_pft_type_series

OUTDIR = OUTDIR_ROOT
os.makedirs(OUTDIR, exist_ok=True)


def main():
    print(f"Loading transient forest-area series ({TRANSIENT})...")
    hist = load_pft_type_series(TRANSIENT, [])

    fut = {}
    for label, case in FUTURE.items():
        print(f"Loading {label} ({case})...")
        fut[label] = load_pft_type_series(case, [])

    # 2026-09-16: drop the DF (deforest counterfactual) line -- its forest
    # area collapses to ~0 by construction (HARVEST_TO=0 across all
    # forest), which compresses the other six scenarios' more subtle
    # differences into a narrow band near the top of the axis.
    DROP_LABELS = {"SSP3-7.0 DF (deforest counterfactual)"}

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(hist["year"], hist["forest_area_frac"], color="k", lw=1.8, label="historical (transient, 1850-2023)")
    for label, d in fut.items():
        if label in DROP_LABELS:
            continue
        style = FUTURE_STYLE[label]
        ax.plot(d["year"], d["forest_area_frac"], lw=1.5, label=label, **style)

    ax.set_xlabel("year")
    ax.set_ylabel("Forest area (% of domain PFT-weighted area)")
    ax.set_title("SEUS 0.5°: forest area change, 1850–2100\n"
                 "(forest = natpft 1-8; % of domain PFT weight, not absolute km²)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, "forest_area_change_1850_2100.png")
    fig.savefig(outpath, dpi=150)
    plt.close(fig)

    print("\nSummary (forest area, % of domain PFT weight):")
    print(f"  1850: {hist['forest_area_frac'][0]:.2f}%")
    print(f"  2023 (transient end): {hist['forest_area_frac'][-1]:.2f}%")
    for label, d in fut.items():
        print(f"  {label} 2024: {d['forest_area_frac'][0]:.2f}%  2100: {d['forest_area_frac'][-1]:.2f}%")
    print(f"\nFigure written to {outpath}")


if __name__ == "__main__":
    main()
