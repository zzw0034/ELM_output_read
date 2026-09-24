"""
4 km GPP maps of one land-use scenario (DF or Default) for all four
SSPs, 2091-2100 mean, no overlays:
  row 1  old run (crit_dayl_stress = 36000 s)
  row 2  new run (38000 s)
  row 3  new - old
one column per SSP; rows 1-2 share one colour scale across all eight panels,
row 3 has its own symmetric scale. Two figures: annual GPP and January GPP.

Reuses the verified readers in analyze_4km_cds38000.py. Run through Slurm:
  sbatch -J DF_4ssp  submit_py.sbatch plot_DF_gpp_4ssp.py            (DF)
  sbatch -J Def_4ssp submit_py.sbatch plot_DF_gpp_4ssp.py Default    (Default)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze_4km_cds38000 import (ALL_SSPS, SSP_LABEL, OUTDIR, PERIODS, LATE, JAN, case_name,
                                  h0_climatology, load_grid)


RUNS = {"DF": ("oldDF", "newDF"), "Default": ("Default", "newDefault")}


def main(landuse):
    old_run, new_run = RUNS[landuse]
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid("ssp585")
    land = W > 0
    F = {}
    for s in ALL_SSPS:
        for run in (old_run, new_run):
            c = case_name(run, s)
            print(f"reading {c}", flush=True)
            ann, mon = h0_climatology(c, "GPP", PERIODS[LATE])
            F[(run, s, "annual")] = np.where(land, ann, np.nan)
            F[(run, s, "jan")] = np.where(land, mon[JAN], np.nan)
            del mon

    for kind, label in (("annual", "Annual GPP"), ("jan", "January GPP (annualised rate)")):
        vmax = np.nanmax([np.nanpercentile(F[(r, s, kind)], 99.5) for r in (old_run, new_run) for s in ALL_SSPS])
        diffs = {s: F[(new_run, s, kind)] - F[(old_run, s, kind)] for s in ALL_SSPS}
        dmax = np.nanmax([np.nanpercentile(np.abs(d), 99.5) for d in diffs.values()])
        fig, axes = plt.subplots(3, 4, figsize=(24, 15))
        for j, s in enumerate(ALL_SSPS):
            for i, (run, cds) in enumerate(((old_run, 36000), (new_run, 38000))):
                ax = axes[i, j]
                pc = ax.pcolormesh(lon, lat, F[(run, s, kind)], cmap="viridis", vmin=0, vmax=vmax,
                                   shading="auto")
                ax.set_aspect("equal")
                ax.set_title(f"{SSP_LABEL[s]} {landuse}, {cds} s", fontsize=11)
                ax.tick_params(labelsize=7)
            ax = axes[2, j]
            pd = ax.pcolormesh(lon, lat, diffs[s], cmap="RdBu", vmin=-dmax, vmax=dmax, shading="auto")
            ax.set_aspect("equal")
            ax.set_title(f"{SSP_LABEL[s]} {landuse}, 38000 - 36000 s", fontsize=11)
            ax.tick_params(labelsize=7)
        fig.colorbar(pc, ax=list(axes[:2, :].ravel()), shrink=0.6, label=f"{label} (gC m$^{{-2}}$ yr$^{{-1}}$)")
        fig.colorbar(pd, ax=list(axes[2, :]), shrink=0.8, label="new - old (gC m$^{-2}$ yr$^{-1}$)")
        fig.suptitle(f"4 km {landuse} {label}, {LATE} mean, all SSPs (no overlays; rows 1-2 share one scale)",
                     fontsize=14)
        out = os.path.join(OUTDIR, f"maps_{landuse}_gpp_{kind}_4ssp.png")
        fig.savefig(out, dpi=130, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out}")


if __name__ == "__main__":
    lu = sys.argv[1] if len(sys.argv) > 1 else "DF"
    if lu not in RUNS:
        sys.exit(f"unknown land use {lu!r}; choose from {list(RUNS)}")
    main(lu)
