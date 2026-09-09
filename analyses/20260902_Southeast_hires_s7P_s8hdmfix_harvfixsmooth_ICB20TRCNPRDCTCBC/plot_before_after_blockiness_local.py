"""
Answer the question this rerun was made to answer: are the 0.25 deg blocks in
Biomass_2010 gone now that the harvest forcing has been smoothed?

Compares, side by side and as a difference:
  before  analyses/20260723_..._harvfix_...        (blocky harvest forcing)
  after   analyses/20260902_..._harvfixsmooth_...  (this run)

for both the harvest forcing itself and the resulting biomass, in 2010 -- the
year whose figure showed the problem. Figures written:

  <Var>BeforeAfter_2010.png       whole domain, before / after / difference
  <Var>BeforeAfterZoom_2010.png   the same three panels over ZOOM_BOX, the
                                  worst-affected area, with the 0.25 deg grid
                                  drawn on top so block edges can be checked
                                  against it directly

Putting a number on "blocky"
----------------------------
LUH2 is native 0.25 deg and the run's grid is 1/24 deg, so exactly 6 fine cells
span one coarse cell, and a downscaled-block artifact must place its
discontinuities on one repeating phase of that 6-cell cycle. So: bin every
adjacent-cell step by its index modulo 6 and normalize by the field's own mean
step. A flat profile means no periodic structure; a spike at one phase means
blocks.

Which phase carries the artifact is *measured*, not assumed. The old run's
AnnualHarvest_2010 is the known-blocky reference, so its own profile defines
the block phases, separately for the west-east and south-north directions.
This matters: the block edge straddles two fine cells rather than landing on
one, and it is not the same pair of phases on both axes.

    block index = mean(profile over block phases)
                  / mean(profile over the other phases)

    1.0 -> steps on the coarse-grid phase look like steps anywhere else

Read the index against the 1850 row, not against 1.0. The surface dataset
carries a little 6-cell structure of its own, so 1850 biomass -- which no
harvest history has touched, and which is bit-identical between the two runs --
is what "no harvest blocks" measures as on this grid.

Sensitivity, stated plainly: the index is decisive for the forcing, where the
blocks cover the whole domain, and only weakly sensitive for biomass, where
they cover a fraction of it and compete with genuine 4 km heterogeneity in the
same step statistics. A domain-wide biomass index that barely moves is
therefore not evidence that nothing changed -- read it next to the zoom figure
and the ZOOM_BOX rows, which is where the signal actually lives.

Runs **locally** (needs cartopy + rioxarray):
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_before_after_blockiness_local.py
"""

import os
import sys

import numpy as np
import rioxarray as rxr
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, TwoSlopeNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSES_DIR = os.path.dirname(SCRIPT_DIR)
NEW_OUT = os.path.join(SCRIPT_DIR, "outputs")
OLD_OUT = os.path.join(
    ANALYSES_DIR,
    "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC",
    "outputs",
)

YEAR = 2010
CYCLE = 6                    # 0.25 deg / (1/24 deg) = 6 fine cells per coarse cell
COARSE_DEG = 0.25
BLOCK_PHASE_THRESHOLD = 1.2  # a phase counts as a block phase when the reference
                             # blocky field's normalized step there exceeds this

# Mississippi/Alabama/Georgia, where the old Biomass_2010 figure's rectangles
# are largest. (west, east, south, north)
ZOOM_BOX = (-89.5, -84.0, 30.4, 33.0)


def read_tif(path: str):
    da = rxr.open_rasterio(path).squeeze("band", drop=True)
    arr = da.values.astype(float)
    nodata = da.rio.nodata
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr, da["y"].values, da["x"].values


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50):
    finite = data[np.isfinite(data)]
    if finite.size == 0 or finite.max() <= finite.min():
        return None
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    return BoundaryNorm(edges, ncolors=256) if len(edges) >= 2 else None


def subset(arr, lat, lon, box):
    """Crop to (west, east, south, north). Also returns the crop's origin
    indices, which the phase bookkeeping needs."""
    w, e, s, n = box
    jy = np.where((lat >= s) & (lat <= n))[0]
    jx = np.where((lon >= w) & (lon <= e))[0]
    return arr[np.ix_(jy, jx)], lat[jy], lon[jx], int(jy[0]), int(jx[0])


# ── Blockiness ───────────────────────────────────────────────────────────

def phase_profile(arr: np.ndarray, axis: int, origin: int = 0) -> np.ndarray:
    """Mean |adjacent-cell step| binned by edge index modulo CYCLE, divided by
    the field's own mean step. axis=1 is west-east, axis=0 south-north.
    *origin* is the array's start index in the full grid, so a cropped array
    still reports phases in the full grid's numbering."""
    d = np.abs(np.diff(arr, axis=axis))
    overall = np.nanmean(d)
    if not np.isfinite(overall) or overall == 0:
        return np.full(CYCLE, np.nan)
    take = (lambda p: d[:, p::CYCLE]) if axis == 1 else (lambda p: d[p::CYCLE, :])
    local = np.array([np.nanmean(take(p)) for p in range(CYCLE)]) / overall
    out = np.empty(CYCLE)
    for p in range(CYCLE):
        out[(origin + p) % CYCLE] = local[p]
    return out


def block_phases(reference: np.ndarray, axis: int) -> np.ndarray:
    """Phases of the 6-cell cycle that the known-blocky reference field jumps
    on. Falls back to the single highest phase if nothing clears the threshold,
    so the metric is always defined."""
    prof = phase_profile(reference, axis)
    idx = np.where(prof >= BLOCK_PHASE_THRESHOLD)[0]
    return idx if idx.size else np.array([int(np.nanargmax(prof))])


def block_index(arr, phases_x, phases_y, origin_y=0, origin_x=0) -> dict:
    """Mean normalized step on the block phases over the mean on the rest,
    pooled across both axes."""
    on, off, profiles = [], [], {}
    for axis, phases, origin, key in ((1, phases_x, origin_x, "profile_x"),
                                      (0, phases_y, origin_y, "profile_y")):
        prof = phase_profile(arr, axis, origin)
        profiles[key] = prof
        mask = np.zeros(CYCLE, dtype=bool)
        mask[phases] = True
        on.append(prof[mask])
        off.append(prof[~mask])
    on_mean = float(np.nanmean(np.concatenate(on)))
    off_mean = float(np.nanmean(np.concatenate(off)))
    return {"index": on_mean / off_mean if off_mean else float("nan"), **profiles}


# ── Figures ──────────────────────────────────────────────────────────────

def three_panel(before, after, lat, lon, *, cmap, units, label,
                title_before, title_after, outfile, draw_coarse_grid=False):
    """Before/after on one shared quantile scale, plus after-minus-before on a
    diverging scale centred at zero."""
    pooled = np.concatenate([
        before[np.isfinite(before)].ravel(), after[np.isfinite(after)].ravel()
    ])
    norm = quantile_boundary_norm(pooled)

    diff = after - before
    lim = float(np.nanpercentile(np.abs(diff[np.isfinite(diff)]), 99)) or 1.0
    diff_norm = TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim)

    fig, axes = plt.subplots(
        1, 3, figsize=(19, 5.5), subplot_kw={"projection": ccrs.PlateCarree()}
    )
    panels = [
        (before, title_before, cmap, norm, label),
        (after, title_after, cmap, norm, label),
        (diff, "after − before", "RdBu_r", diff_norm, f"Δ {label}"),
    ]
    for ax, (data, title, cm, nm, lab) in zip(axes, panels):
        mesh = ax.pcolormesh(lon, lat, data, cmap=cm, norm=nm,
                             shading="auto", transform=ccrs.PlateCarree())
        ax.add_feature(cfeature.STATES, linewidth=0.4, edgecolor="0.3")
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        if draw_coarse_grid:
            for g in np.arange(np.ceil(lon.min() / COARSE_DEG) * COARSE_DEG,
                               lon.max(), COARSE_DEG):
                ax.axvline(g, color="k", lw=0.3, alpha=0.35)
            for g in np.arange(np.ceil(lat.min() / COARSE_DEG) * COARSE_DEG,
                               lat.max(), COARSE_DEG):
                ax.axhline(g, color="k", lw=0.3, alpha=0.35)
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()],
                      crs=ccrs.PlateCarree())
        ax.set_title(title, fontsize=11)
        cb = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.05, shrink=0.9)
        cb.set_label(f"{lab} ({units})", fontsize=9)
        cb.ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {os.path.basename(outfile)}")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    ref_path = os.path.join(OLD_OUT, f"AnnualHarvest_{YEAR}.tif")
    if not os.path.exists(ref_path):
        sys.exit(f"missing the blocky reference field {ref_path}")
    reference, _, _ = read_tif(ref_path)
    px = block_phases(reference, axis=1)
    py = block_phases(reference, axis=0)
    print(f"Block phases measured from the old AnnualHarvest_{YEAR}: "
          f"west-east {px.tolist()}, south-north {py.tolist()}")

    lines = [
        f"Blockiness of the {COARSE_DEG} deg grid, year {YEAR}.",
        "Adjacent-cell steps binned by index modulo 6 (6 fine cells per 0.25 deg),",
        "normalized by each field's own mean step. Block phases are measured from",
        f"the old run's AnnualHarvest_{YEAR}: west-east {px.tolist()}, "
        f"south-north {py.tolist()}.",
        "index = mean(normalized step on block phases) / mean(on the other phases).",
        "Read each index against the 1850 biomass row, which is the "
        "no-harvest-blocks baseline",
        "for this grid, not against 1.0. The index is decisive for the forcing "
        "and only weakly",
        "sensitive for biomass -- see the module docstring.",
        f"zoom box (W,E,S,N) = {ZOOM_BOX}",
        "",
        f"{'field':22s} {'run':22s} {'whole domain':>13s} {'zoom box':>10s}",
    ]

    # the two fields the rerun was meant to change, plus 1850 biomass as the
    # no-harvest-blocks baseline
    targets = [
        ("AnnualHarvest", YEAR, "Annual wood harvest", "unitless", "OrRd", True),
        ("Biomass", YEAR, "Aboveground biomass (TOTVEGC_ABG)", "kgC/m^2", "viridis", True),
        ("Biomass", 1850, "Aboveground biomass (TOTVEGC_ABG)", "kgC/m^2", "viridis", False),
    ]

    for prefix, year, label, units, cmap, make_figures in targets:
        old_path = os.path.join(OLD_OUT, f"{prefix}_{year}.tif")
        new_path = os.path.join(NEW_OUT, f"{prefix}_{year}.tif")
        if not (os.path.exists(old_path) and os.path.exists(new_path)):
            print(f"{prefix}_{year}: missing a GeoTIFF; skipping")
            continue

        before, lat, lon = read_tif(old_path)
        after, lat2, lon2 = read_tif(new_path)
        assert before.shape == after.shape, f"{prefix}_{year}: grid mismatch"
        assert np.allclose(lat, lat2) and np.allclose(lon, lon2), \
            f"{prefix}_{year}: coordinate mismatch between the two runs"

        print(f"\n{prefix}_{year}")
        for run_label, field in (("before (harvfix)", before),
                                 ("after  (harvfixsmooth)", after)):
            whole = block_index(field, px, py)
            crop, _, _, oy, ox = subset(field, lat, lon, ZOOM_BOX)
            zoom = block_index(crop, px, py, origin_y=oy, origin_x=ox)
            row = (f"{prefix + '_' + str(year):22s} {run_label:22s} "
                   f"{whole['index']:13.3f} {zoom['index']:10.3f}")
            print("  " + row.strip())
            print(f"    phase profile W-E {np.round(whole['profile_x'], 3).tolist()}  "
                  f"S-N {np.round(whole['profile_y'], 3).tolist()}")
            lines.append(row)

        if make_figures:
            three_panel(
                before, after, lat, lon,
                cmap=cmap, units=units, label=label,
                title_before=f"{label} {year} — harvfix (blocky forcing)",
                title_after=f"{label} {year} — harvfixsmooth",
                outfile=os.path.join(NEW_OUT, f"{prefix}BeforeAfter_{year}.png"),
            )
            cb, clat, clon, _, _ = subset(before, lat, lon, ZOOM_BOX)
            ca, _, _, _, _ = subset(after, lat, lon, ZOOM_BOX)
            three_panel(
                cb, ca, clat, clon,
                cmap=cmap, units=units, label=label,
                title_before=f"{label} {year} — harvfix (0.25° grid drawn)",
                title_after=f"{label} {year} — harvfixsmooth",
                outfile=os.path.join(NEW_OUT, f"{prefix}BeforeAfterZoom_{year}.png"),
                draw_coarse_grid=True,
            )

    txt = os.path.join(NEW_OUT, f"blockiness_metric_{YEAR}.txt")
    with open(txt, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nWrote {txt}")


if __name__ == "__main__":
    main()
