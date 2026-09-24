"""
Legacy asset fig02: spatial maps of management stock differences.

Feeds new Main Figure 3 / Results 3.3 and supplementary maps. RF is a
restoration/protection bundle; Default-DF is an idealized avoided-loss bound.
Existing maps use the legacy cohort in common.py. Verify case provenance
and the known daylength discontinuity before attributing fine-scale detail
to improved spatial realism. Quantitative observational skill is separate.

Usage inside an approved Slurm allocation:
    python code/fig02_offset_potential_maps.py [0.5deg|4km] [variable]
"""
import os
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import xarray as xr

from common import (HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, OFFSET_DEFS,
                    OUTDIR, load_mean_map, h0_files, area_weights)

Y0, Y1 = 2091, 2100


def make_axes(ax):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else "0.5deg"
    var = sys.argv[2] if len(sys.argv) > 2 else "TOTECOSYSC"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)
    os.makedirs(OUTDIR, exist_ok=True)

    needed = sorted({c for pair in OFFSET_DEFS.values() for c in pair})
    maps = {}
    lon = lat = None
    for label in needed:
        print(f"  loading {label} ({cases[label]}) {var} {Y0}-{Y1} ...")
        this_lon, this_lat, m = load_mean_map(cases[label], var, Y0, Y1, subdir=subdir)
        if lon is None:
            lon, lat = this_lon, this_lat
        else:
            # Fixed 2026-09-15 (Codex review): map subtraction below assumed
            # same-shape arrays from different cases were on the same grid
            # without checking. All cases at a given resolution share a
            # surface dataset so this should always hold -- but assert it
            # rather than silently subtracting misaligned grids if it ever
            # doesn't.
            assert np.array_equal(lon, this_lon) and np.array_equal(lat, this_lat), \
                f"{label}'s lon/lat grid differs from the first case's -- cannot subtract maps"
        maps[label] = m

    offsets = {name: maps[pos] - maps[neg] for name, (pos, neg) in OFFSET_DEFS.items()}

    # Land-area weights, and a land mask. Ocean/masked gridcells come back as
    # 0.0 rather than NaN in these files, so statistics computed with only an
    # isfinite() filter silently include a large block of zeros -- that is what
    # made every practice's median come out as exactly 0.0 in the first run of
    # this script. Mask to landfrac>0 and area-weight (see the project's
    # weighted_vs_unweighted_spatial_means_qa lesson).
    ds0 = xr.open_dataset(h0_files(cases["SSP3-7.0"], subdir)[0], decode_times=False)
    w = area_weights(ds0)
    ds0.close()
    land = w > 0

    # Shared symmetric colour scale across RF/RH management bundles; DF's
    # domain total (~9.9 PgC) is ~2x RF's (~5.0 PgC) and ~10x RH's (~1.0 PgC)
    # -- not orders of magnitude -- but that's still enough to wash out RH on
    # a shared scale, so DF gets its own (stated on the colourbar).
    deployable = [v[land] for k, v in offsets.items() if "Default - DF" not in k]
    vmax_dep = np.nanpercentile(np.abs(np.concatenate(deployable)), 99)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    for ax, (name, d) in zip(axes, offsets.items()):
        make_axes(ax)
        is_df = "Default - DF" in name
        vmax = np.nanpercentile(np.abs(d[land]), 99) if is_df else vmax_dep
        pc = ax.pcolormesh(lon, lat, d, transform=ccrs.PlateCarree(),
                           cmap="BrBG", vmin=-vmax, vmax=vmax, shading="auto")
        cb = fig.colorbar(pc, ax=ax, orientation="horizontal", pad=0.05, shrink=0.85)
        cb.set_label(f"{var} offset (gC m$^{{-2}}$)" + ("  [own scale]" if is_df else ""),
                     fontsize=8)
        ax.set_title(name, fontsize=10)

    fig.suptitle(f"SEUS {res} SSP3-7.0: spatial carbon benefits, {Y0}-{Y1} mean "
                 f"({var}; DF is an idealized avoided-loss bound)", fontsize=12, y=1.02)
    fig.tight_layout()
    out = os.path.join(OUTDIR, f"fig02_offset_potential_maps_{var}_{res}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)

    def area_weighted_percentile(vals, ww, q):
        """Area-weighted percentile (q in [0,100]) via the weighted CDF.
        Fixed 2026-09-15 (Codex review): the median/p95 below used to be
        np.nanmedian/np.nanpercentile -- unweighted, i.e. one vote per
        GRIDCELL regardless of physical size -- while the mean in the same
        row was area-weighted. Inconsistent within one printed row."""
        order = np.argsort(vals)
        v, wsort = vals[order], ww[order]
        cw = np.cumsum(wsort) - 0.5 * wsort
        cw /= wsort.sum()
        return float(np.interp(q / 100.0, cw, v))

    print(f"\n--- Spatial offset statistics ({var}, gC/m2, {Y0}-{Y1}, land cells only, "
          f"ALL area-weighted) ---")
    print(f"{'practice':40s} {'area-wt mean':>13} {'area-wt median':>15} {'area-wt p95':>12} "
          f"{'max':>9} {'% of land area >1000':>21}")
    for name, d in offsets.items():
        flat = name.replace("\n", " ")
        vals, ww = d[land], w[land]
        good = np.isfinite(vals)
        v, wv = vals[good], ww[good]
        awmean = np.nansum(v * wv) / np.nansum(wv)
        awmedian = area_weighted_percentile(v, wv, 50)
        awp95 = area_weighted_percentile(v, wv, 95)
        frac_big = 100 * np.nansum(wv[v > 1000]) / np.nansum(wv)
        print(f"{flat:40s} {awmean:13.1f} {awmedian:15.1f} "
              f"{awp95:12.1f} {np.nanmax(v):9.1f} "
              f"{frac_big:20.1f}%")

    print(f"\nFigure written to {out}")


if __name__ == "__main__":
    main()
