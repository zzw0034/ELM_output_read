"""
Decadal-spaced spatial maps for the 4km SEUS SSP1-1.9 future run
20260917_seus_4km_fut_ssp119 (2024-2100) -- a first-look sanity check of the
simulation, not a publication figure set.

For each of GPP, NPP, TOTSOMC_1m (soil organic C to 1m), FAREA_BURNED
(annualized burned-area fraction), and PFT_FIRE_CLOSS (fire C loss), plots
one figure with 5 panels: the day-weighted annual mean for 2024, 2044, 2064,
2084, and 2100 (the last panel is only 16 years after 2084, since the run
ends in 2100, not a full 20-year step). Each panel reads a single year's own
h0 file directly -- no multi-year averaging -- so this is a single-year
snapshot per panel, not a decadal climatology.

Must run via Slurm (sbatch), never on the Pathfinder login node -- see
common.py docstring. Figures written to OUTDIR_ROOT (this case's figure/
mirror on scratch); rsync back to the local figure/ folder to view.
"""
import os

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import VAR_SPECS, SNAPSHOT_YEARS, OUTDIR_ROOT, load_year_map

os.makedirs(OUTDIR_ROOT, exist_ok=True)


def make_axes_map(ax):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def snapshot_series_map(var, units, cmap, kind):
    print(f"  loading {var} for years {SNAPSHOT_YEARS}...")
    lon = lat = None
    maps = {}
    for year in SNAPSHOT_YEARS:
        lon, lat, m = load_year_map(var, year, kind)
        maps[year] = m

    vmin = np.nanmin([np.nanmin(m) for m in maps.values()])
    vmax = np.nanmax([np.nanmax(m) for m in maps.values()])

    fig, axes = plt.subplots(1, len(SNAPSHOT_YEARS), figsize=(4 * len(SNAPSHOT_YEARS), 5),
                              subplot_kw={"projection": ccrs.PlateCarree()})
    for ax, year in zip(axes, SNAPSHOT_YEARS):
        make_axes_map(ax)
        pc = ax.pcolormesh(lon, lat, maps[year], transform=ccrs.PlateCarree(),
                            cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
        ax.set_title(str(year), fontsize=10)

    fig.colorbar(pc, ax=list(axes), orientation="horizontal", pad=0.06, shrink=0.6,
                 label=f"{var} ({units})")
    fig.suptitle(f"SEUS 4km SSP1-1.9 (20260917_seus_4km_fut_ssp119): "
                 f"{var} annual mean, 2024-2100 snapshots",
                 fontsize=13)
    fig.savefig(os.path.join(OUTDIR_ROOT, f"spatial_snapshots_{var}.png"), dpi=150,
                bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote spatial_snapshots_{var}.png "
          f"(range [{vmin:.4g}, {vmax:.4g}] {units})")


def main():
    for var, units, cmap, kind in VAR_SPECS:
        print(f"Building snapshot map for {var}...")
        snapshot_series_map(var, units, cmap, kind)
    print(f"Figures written to {OUTDIR_ROOT}")


if __name__ == "__main__":
    main()
