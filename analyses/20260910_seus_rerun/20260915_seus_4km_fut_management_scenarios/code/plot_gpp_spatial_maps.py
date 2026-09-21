"""
GPP spatial sanity-check maps for the 6 4km SEUS management-scenario cases
that were blocked by the PCT_NAT_PFT landuse bug (fixed and rerun
2026-09-20/21 -- see ELM_Futu_landuseInput/future_runs/docs/
BLOCKER_pct_nat_pft_sum.md). Purpose is a first-look QA check that the
rebuilt-landuse reruns produce physically sane GPP, not a publication figure.

Two products, each a 2 (DF/RH) x 3 (SSP1-1.9/SSP2-4.5/SSP5-8.5) grid with a
shared color scale so patterns are directly comparable:
  1. 2024 (first simulated year) -- checks initialization looks sane.
  2. 2091-2100 mean (end of century) -- checks the long-term state.

Must run via Slurm (sbatch), never on the Pathfinder login node -- see
common.py docstring. Figures written to OUTDIR_ROOT (scratch mirror);
rsync back to the local figure/ folder to view.
"""
import os

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import CASES, OUTDIR_ROOT, load_mean_map

os.makedirs(OUTDIR_ROOT, exist_ok=True)

ROWS = ["DF", "RH"]
COLS = ["SSP1-1.9", "SSP2-4.5", "SSP5-8.5"]


def make_axes_map(ax):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def grid_map(year_min, year_max, label, outfile):
    print(f"Loading GPP for {label} ({year_min}-{year_max})...")
    maps = {}
    lon = lat = None
    for row in ROWS:
        for col in COLS:
            key = f"{col} {row}"
            case = CASES[key]
            lon, lat, m = load_mean_map(case, "GPP", year_min, year_max)
            maps[(row, col)] = m
            print(f"  {key} ({case}): mean={np.nanmean(m):.1f} "
                  f"range=[{np.nanmin(m):.1f}, {np.nanmax(m):.1f}]")

    vmin = np.nanmin([np.nanmin(m) for m in maps.values()])
    vmax = np.nanmax([np.nanmax(m) for m in maps.values()])

    fig, axes = plt.subplots(2, 3, figsize=(15, 9),
                              subplot_kw={"projection": ccrs.PlateCarree()})
    for i, row in enumerate(ROWS):
        for j, col in enumerate(COLS):
            ax = axes[i, j]
            make_axes_map(ax)
            pc = ax.pcolormesh(lon, lat, maps[(row, col)], transform=ccrs.PlateCarree(),
                                cmap="viridis", vmin=vmin, vmax=vmax, shading="auto")
            ax.set_title(f"{col} {row}", fontsize=10)

    fig.colorbar(pc, ax=list(axes.flat), orientation="horizontal", pad=0.05, shrink=0.6,
                 label="GPP (gC m$^{-2}$ yr$^{-1}$)")
    fig.suptitle(f"SEUS 4km management scenarios: GPP annual mean, {label}", fontsize=13)
    fig.savefig(os.path.join(OUTDIR_ROOT, outfile), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {outfile}  (shared color range [{vmin:.1f}, {vmax:.1f}])")


def main():
    grid_map(2024, 2024, "2024 (first year)", "gpp_management_scenarios_2024.png")
    grid_map(2091, 2100, "2091-2100 mean (end of century)",
              "gpp_management_scenarios_2091_2100.png")
    print(f"Figures written to {OUTDIR_ROOT}")


if __name__ == "__main__":
    main()
