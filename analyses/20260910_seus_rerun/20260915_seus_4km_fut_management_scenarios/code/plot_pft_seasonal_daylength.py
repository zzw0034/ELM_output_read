"""
PFT-resolved winter/summer GPP maps -- the decisive test that the 30.833N
step comes from ELM's stress-deciduous phenology threshold
(crit_dayl_stress = 36000 s = 10 hr) and nothing else.

Design: everything is read from ONE simulation (SSP5-8.5 Default), so the
gridcells, climate, soil, land cover and executable are identical across
all four panels. The ONLY thing that changes between the left and right
columns is which PFTs you look at:

  - GRASS PFTs (natpft 12/13/14) are stress-deciduous -> subject to the
    crit_dayl_stress force-offset -> must show a hard step at 30.833N in
    January and no step in July.
  - TREE PFTs (natpft 1-8) are evergreen or season-deciduous -> governed
    by crit_dayl (39300 s, whose threshold latitude is 18.06N, i.e. south
    of the whole domain) -> must show NO step at 30.833N in either month.

If grass steps and trees do not, in the same run and the same cells, the
mechanism is isolated with no confounding.

Reads h1 (PFT-level, pft dim ~2.44M, ~7.5 GB/file); only two month-slices
of GPP per file are pulled, so the memory footprint stays small. Must run
via Slurm, never on the login node.

Full write-up: ../../../CRIT_DAYL_STRESS_ARTIFACT.md
"""
import glob
import os
import re

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from common import OUTDIR_ROOT

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
CASE = "20260917_seus_4km_fut_ssp585"          # Default: has BOTH trees and grass
YEARS = (2097, 2099)                            # 3 years is plenty to average noise
THRESHOLD_LAT = 30.833
SEC_PER_YEAR_NOLEAP = 365 * 86400.0
EXTENT = [-92, -75, 24, 37]

GROUPS = {
    "Grass (stress-deciduous, natpft 12-14)": [12, 13, 14],
    "Trees (natpft 1-8)": list(range(1, 9)),
}
MONTHS = [(0, "January"), (6, "July")]


def _year_of(f):
    return int(re.search(r"\.h1\.(\d+)-", f).group(1))


def main():
    d = os.path.join(CASE_ROOT, CASE, "run")
    files = sorted(f for f in glob.glob(os.path.join(d, f"{CASE}.elm.h1.*.nc"))
                   if not f.endswith(".loc") and YEARS[0] <= _year_of(f) <= YEARS[1])
    print(f"{len(files)} h1 files: {[_year_of(f) for f in files]}")

    # grid from the matching h0 file
    h0 = sorted(f for f in glob.glob(os.path.join(d, f"{CASE}.elm.h0.*.nc"))
                if not f.endswith(".loc") and _year_of(f.replace(".h0.", ".h1.")) == YEARS[1])[0]
    with xr.open_dataset(h0, decode_times=False) as ds0:
        lat = ds0["lat"].values
        lon = ds0["lon"].values
    nlat, nlon = len(lat), len(lon)
    print(f"grid {nlat} x {nlon}")

    # accumulate weighted GPP per (group, month) on the 2D grid
    acc = {(g, mi): np.zeros((nlat, nlon)) for g in GROUPS for mi, _ in MONTHS}
    wsum = {(g, mi): np.zeros((nlat, nlon)) for g in GROUPS for mi, _ in MONTHS}

    for f in files:
        print(f"reading {os.path.basename(f)}...", flush=True)
        ds = xr.open_dataset(f, decode_times=False)
        itype = ds["pfts1d_itype_veg"].values.astype(int)
        ixy = ds["pfts1d_ixy"].values.astype(int) - 1     # to 0-based
        jxy = ds["pfts1d_jxy"].values.astype(int) - 1
        wt = ds["pfts1d_wtgcell"].values
        wt = np.where(np.isfinite(wt), wt, 0.0)
        for mi, _mname in MONTHS:
            gpp = ds["GPP"].values[mi] * SEC_PER_YEAR_NOLEAP
            good = np.isfinite(gpp) & (wt > 0)
            for gname, types in GROUPS.items():
                sel = good & np.isin(itype, types)
                if sel.sum() == 0:
                    continue
                np.add.at(acc[(gname, mi)], (jxy[sel], ixy[sel]), gpp[sel] * wt[sel])
                np.add.at(wsum[(gname, mi)], (jxy[sel], ixy[sel]), wt[sel])
        ds.close()

    maps = {}
    for key in acc:
        with np.errstate(invalid="ignore", divide="ignore"):
            m = np.where(wsum[key] > 0, acc[key] / np.where(wsum[key] > 0, wsum[key], 1), np.nan)
        maps[key] = m

    # --- figure: rows = month, cols = PFT group ---
    fig, axes = plt.subplots(2, 2, figsize=(17, 12),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    gnames = list(GROUPS.keys())
    for i, (mi, mname) in enumerate(MONTHS):
        row = [maps[(g, mi)] for g in gnames]
        vmin = float(np.nanmin([np.nanmin(v) for v in row]))
        vmax = float(np.nanmax([np.nanmax(v) for v in row]))
        for j, gname in enumerate(gnames):
            ax = axes[i, j]
            ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
            ax.set_extent(EXTENT, crs=ccrs.PlateCarree())
            pc = ax.pcolormesh(lon, lat, maps[(gname, mi)], transform=ccrs.PlateCarree(),
                               cmap="viridis", vmin=vmin, vmax=vmax, shading="auto")
            ax.plot(EXTENT[:2], [THRESHOLD_LAT] * 2, color="red", linewidth=1.0,
                    linestyle="--", transform=ccrs.PlateCarree())
            ax.set_title(f"{mname} — {gname}", fontsize=11)
        fig.colorbar(pc, ax=list(axes[i, :]), orientation="vertical", pad=0.02, shrink=0.85,
                     label=f"{mname} GPP (gC m$^{{-2}}$ yr$^{{-1}}$)")

    fig.suptitle(f"PFT-resolved test, ALL from one run ({CASE}, {YEARS[0]}-{YEARS[1]}):\n"
                 "grass is stress-deciduous and steps at 30.833N in January only; "
                 "trees use a different threshold and never step",
                 fontsize=13)
    out = os.path.join(OUTDIR_ROOT, "gpp_pft_jan_jul_daylength.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # --- quantitative row transect across the threshold, per group/month ---
    print(f"\nRow transect around the threshold ({THRESHOLD_LAT}N):")
    for gname in gnames:
        for mi, mname in MONTHS:
            m = maps[(gname, mi)]
            print(f"\n  --- {gname} / {mname} ---")
            prev = None
            for i in range(160, 170):
                v = np.nanmean(m[i][np.isfinite(m[i])])
                d = "" if prev is None else f"  d={v - prev:+.1f}"
                mark = "  <== threshold" if i == 164 else ""
                print(f"    row={i} lat={lat[i]:.3f}  GPP={v:.1f}{d}{mark}")
                prev = v


if __name__ == "__main__":
    main()
