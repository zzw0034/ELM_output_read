"""
Legacy asset fig04: regional totals and native/aggregated spatial fields.

Feeds new Main Figure 2 totals and Main Figure 3 heterogeneity. The legacy
grids were documented as 12:1 nested with equal total land area; recheck for
the selected manuscript cohort. Equal area does not isolate a resolution
effect when parameter files, restarts or other configuration differ.

Panels A/B compare regional stocks/benefits. Panels C/D compare the DF
avoided-loss bound at native 4 km, 4 km aggregated to 0.5 degrees, and native
0.5 degrees. Extend spatial diagnostics to RF for the planned main story.
Extra distribution tails establish modeled heterogeneity, not accuracy.
Known daylength-threshold structure requires separate sensitivity checks.

This script does not evaluate observations or compare equal-area selections.
Some printed percentiles and RMS statistics are not area-weighted; audit
before publication. See FIGURE_PLAN.md and AI_HANDOFF.md.

Usage inside an approved Slurm allocation:
    python fig04_resolution_comparison.py
"""
import os

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from common import (HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, OFFSET_DEFS,
                    OFFSET_COLORS, OUTDIR, h0_files, area_weights, load_mean_map,
                    load_cache, cache_exists, load_annual_series, save_cache)

BLOCK = 12  # 4 km cells per 0.5 deg cell, each direction
Y0, Y1 = 2091, 2100
VARS = ["TOTECOSYSC", "TOTVEGC", "TOTSOMC"]
SCEN = ["SSP3-7.0", "SSP3-7.0 RF", "SSP3-7.0 DF", "SSP3-7.0 RH"]


def get_series(case, subdir, res):
    key = f"{res}__{case}__ecosysc"
    if cache_exists(key):
        return load_cache(key)
    print(f"  loading {case} ({res}) ...")
    s = load_annual_series(case, VARS, subdir=subdir)
    save_cache(s, key)
    return s


def aggregate_to_halfdeg(field_4km, w_4km):
    """Area-weighted 12x12 block mean of a 4 km field onto the 0.5 deg grid."""
    ny, nx = field_4km.shape
    assert ny % BLOCK == 0 and nx % BLOCK == 0, (ny, nx)
    f = np.where(np.isfinite(field_4km), field_4km, 0.0)
    ww = np.where(np.isfinite(w_4km), w_4km, 0.0)
    fb = (f * ww).reshape(ny // BLOCK, BLOCK, nx // BLOCK, BLOCK).sum(axis=(1, 3))
    wb = ww.reshape(ny // BLOCK, BLOCK, nx // BLOCK, BLOCK).sum(axis=(1, 3))
    out = np.full_like(fb, np.nan, dtype=float)
    good = wb > 0
    out[good] = fb[good] / wb[good]
    return out, wb


def make_axes(ax):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    series = {}
    for res, (cases, subdir) in [("0.5deg", (HALFDEG, HALFDEG_SUBDIR)),
                                 ("4km", (FOURKM, FOURKM_SUBDIR))]:
        series[res] = {s: get_series(cases[s], subdir, res) for s in SCEN}

    # ---- Panel A + B ------------------------------------------------------
    fig = plt.figure(figsize=(16, 11))
    axA = fig.add_subplot(2, 2, 1)
    for res, ls in [("0.5deg", "-"), ("4km", "--")]:
        for s in SCEN:
            d = series[res][s]
            axA.plot(d["year"], d["TOTECOSYSC_PgC"], ls=ls, lw=1.4,
                     label=f"{s} ({res})" if s == "SSP3-7.0" or res == "0.5deg" else None)
    axA.set_xlabel("year")
    axA.set_ylabel("Domain total ecosystem C (PgC)")
    axA.set_title("A. Total ecosystem carbon: solid = 0.5°, dashed = 4 km", fontsize=10)
    axA.grid(alpha=0.3)
    axA.legend(fontsize=7)

    axB = fig.add_subplot(2, 2, 2)
    names = list(OFFSET_DEFS.keys())
    x = np.arange(len(names))
    width = 0.35
    vals = {}
    for i, res in enumerate(["0.5deg", "4km"]):
        v = []
        for name in names:
            pos, neg = OFFSET_DEFS[name]
            end = series[res][pos]["year"] >= Y0
            v.append(float(np.nanmean(series[res][pos]["TOTECOSYSC_PgC"][end] -
                                      series[res][neg]["TOTECOSYSC_PgC"][end])))
        vals[res] = v
        axB.bar(x + i * width, v, width=width, label=res,
                color=["tab:blue", "tab:cyan"][i], edgecolor="k", linewidth=0.4)
    for j, name in enumerate(names):
        pct = 100 * (vals["4km"][j] - vals["0.5deg"][j]) / vals["0.5deg"][j]
        axB.text(x[j] + width / 2, max(vals["0.5deg"][j], vals["4km"][j]) * 1.03,
                 f"{pct:+.1f}%", ha="center", fontsize=8)
    axB.set_xticks(x + width / 2)
    axB.set_xticklabels([n.replace("\n", " ") for n in names], rotation=12, fontsize=8)
    axB.set_ylabel("Offset potential, 2091-2100 (PgC)")
    axB.set_title("B. Regional stock benefits in the two configurations", fontsize=10)
    axB.grid(alpha=0.3, axis="y")
    axB.legend(fontsize=8)

    # ---- Panels C + D: spatial, on a fair footing -------------------------
    print("  loading 2091-2100 maps ...")
    maps = {}
    for res, (cases, subdir) in [("0.5deg", (HALFDEG, HALFDEG_SUBDIR)),
                                 ("4km", (FOURKM, FOURKM_SUBDIR))]:
        for s in ["SSP3-7.0", "SSP3-7.0 DF"]:
            lon, lat, m = load_mean_map(cases[s], "TOTECOSYSC", Y0, Y1, subdir=subdir)
            maps[(res, s)] = (lon, lat, m)

    ds05 = xr.open_dataset(h0_files(HALFDEG["SSP3-7.0"], HALFDEG_SUBDIR)[0], decode_times=False)
    w05 = area_weights(ds05); ds05.close()
    ds4k = xr.open_dataset(h0_files(FOURKM["SSP3-7.0"], FOURKM_SUBDIR)[0], decode_times=False)
    w4k = area_weights(ds4k); ds4k.close()

    # Forest-preservation offset (Default - DF) at each resolution.
    off05 = maps[("0.5deg", "SSP3-7.0")][2] - maps[("0.5deg", "SSP3-7.0 DF")][2]
    off4k = maps[("4km", "SSP3-7.0")][2] - maps[("4km", "SSP3-7.0 DF")][2]
    off4k_agg, w_agg = aggregate_to_halfdeg(off4k, w4k)

    lon05, lat05 = maps[("0.5deg", "SSP3-7.0")][0], maps[("0.5deg", "SSP3-7.0")][1]
    diff = off4k_agg - off05
    land05 = w05 > 0

    axC = fig.add_subplot(2, 2, 3, projection=ccrs.PlateCarree())
    make_axes(axC)
    v = np.nanpercentile(np.abs(diff[land05]), 99)
    pc = axC.pcolormesh(lon05, lat05, diff, transform=ccrs.PlateCarree(),
                        cmap="RdBu_r", vmin=-v, vmax=v, shading="auto")
    cb = fig.colorbar(pc, ax=axC, orientation="horizontal", pad=0.05, shrink=0.85)
    cb.set_label("4 km aggregated − native 0.5° (gC m$^{-2}$)", fontsize=8)
    axC.set_title("C. Common-support disagreement\n(avoided-loss upper bound, "
                  "4 km aggregated to the 0.5° grid)", fontsize=10)

    axD = fig.add_subplot(2, 2, 4)
    bins = np.linspace(0, np.nanpercentile(off4k[w4k > 0], 99.5), 60)
    axD.hist(off4k[w4k > 0], bins=bins, weights=w4k[w4k > 0], density=True,
             histtype="step", lw=1.6, label="native 4 km")
    axD.hist(off4k_agg[land05], bins=bins, weights=w_agg[land05], density=True,
             histtype="step", lw=1.6, label="4 km aggregated to 0.5°")
    axD.hist(off05[land05], bins=bins, weights=w05[land05], density=True,
             histtype="step", lw=1.6, label="native 0.5°")
    axD.set_xlabel("Avoided-loss upper bound (gC m$^{-2}$)")
    axD.set_ylabel("Area-weighted density")
    axD.set_title("D. Native and aggregated distributions\n"
                  "Modeled heterogeneity and aggregation effects", fontsize=10)
    axD.grid(alpha=0.3)
    axD.legend(fontsize=8)

    fig.suptitle("SEUS SSP3-7.0: regional consistency and spatial heterogeneity", fontsize=13)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "fig04_resolution_comparison.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)

    # ---- numbers ----------------------------------------------------------
    def wmean(field, ww):
        m = np.isfinite(field) & (ww > 0)
        return float(np.nansum(field[m] * ww[m]) / np.nansum(ww[m]))

    print("\n--- Domain totals, 2091-2100 mean (PgC) ---")
    print(f"{'scenario':16s} {'0.5deg':>10} {'4km':>10} {'4km-0.5deg':>12} {'%':>8}")
    for s in SCEN:
        a = float(np.nanmean(series["0.5deg"][s]["TOTECOSYSC_PgC"][series["0.5deg"][s]["year"] >= Y0]))
        b = float(np.nanmean(series["4km"][s]["TOTECOSYSC_PgC"][series["4km"][s]["year"] >= Y0]))
        print(f"{s:16s} {a:10.3f} {b:10.3f} {b-a:12.3f} {100*(b-a)/a:7.1f}%")

    print("\n--- Offset potential, 2091-2100 (PgC) ---")
    for j, name in enumerate(names):
        flat = name.replace("\n", " ")
        print(f"{flat:40s} 0.5deg={vals['0.5deg'][j]:7.3f}  4km={vals['4km'][j]:7.3f}  "
              f"diff={100*(vals['4km'][j]-vals['0.5deg'][j])/vals['0.5deg'][j]:+6.1f}%")

    print("\n--- Spatial, forest-preservation offset (gC/m2) ---")
    print(f"  native 0.5deg      : area-wt mean {wmean(off05, w05):8.1f}  "
          f"p99 {np.nanpercentile(off05[land05], 99):8.1f}  max {np.nanmax(off05[land05]):8.1f}")
    print(f"  4km aggregated     : area-wt mean {wmean(off4k_agg, w_agg):8.1f}  "
          f"p99 {np.nanpercentile(off4k_agg[land05], 99):8.1f}  max {np.nanmax(off4k_agg[land05]):8.1f}")
    print(f"  native 4km         : area-wt mean {wmean(off4k, w4k):8.1f}  "
          f"p99 {np.nanpercentile(off4k[w4k > 0], 99):8.1f}  max {np.nanmax(off4k[w4k > 0]):8.1f}")
    print("\n  If 'native 4km' has a much higher p99/max than '4km aggregated' while their")
    print("  area-weighted means agree, the extra extremes are sub-0.5-degree heterogeneity")
    print("  removed by aggregation. This does not establish accuracy or isolate grid spacing")
    print("  from configuration differences; check the known daylength artifact as well.")
    print(f"\n  RMS of (4km aggregated - native 0.5deg) over land: "
          f"{np.sqrt(np.nanmean(diff[land05]**2)):.1f} gC/m2")

    print(f"\nFigure written to {out}")


if __name__ == "__main__":
    main()
