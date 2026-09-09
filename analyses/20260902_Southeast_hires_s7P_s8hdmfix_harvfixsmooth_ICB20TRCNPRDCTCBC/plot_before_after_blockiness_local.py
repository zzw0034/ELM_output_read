"""
Answer the question this rerun was made to answer: are the 0.25 deg blocks in
Biomass_2010 gone after the harvest forcing was smoothed?

Compares, side by side and as a difference:
  before  analyses/20260723_..._harvfix_...   (blocky harvest forcing)
  after   analyses/20260902_..._harvfixsmooth_... (this run)

for both the harvest forcing itself and the resulting biomass, in 2010 (the
year whose figure showed the problem).

It also puts a number on "blocky", instead of leaving it to the eye. LUH2 is
native 0.25 deg and the run's grid is ~1/24 deg, so a downscaled-block artifact
puts its discontinuities on grid lines that coincide with 0.25 deg boundaries
and nowhere else. The metric is the mean absolute step across cell edges that
fall on a 0.25 deg boundary, divided by the mean absolute step across all other
cell edges:

    1.0  -> steps at coarse boundaries look like steps anywhere else: no blocks
    >>1  -> the field jumps specifically at 0.25 deg boundaries: blocks

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
COARSE_DEG = 0.25          # LUH2 native resolution
EDGE_TOL_FRAC = 0.25       # a cell edge counts as "on a coarse boundary" if it
                           # lies within this fraction of a fine cell of one


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


def _edge_is_on_coarse_boundary(coord: np.ndarray) -> np.ndarray:
    """For 1-D cell centers, return a bool per interior edge (len n-1) saying
    whether that edge sits on a COARSE_DEG boundary."""
    edges = 0.5 * (coord[:-1] + coord[1:])
    spacing = float(np.abs(np.median(np.diff(coord))))
    dist = np.abs(edges / COARSE_DEG - np.round(edges / COARSE_DEG)) * COARSE_DEG
    return dist <= EDGE_TOL_FRAC * spacing


def blockiness_ratio(arr: np.ndarray, lat: np.ndarray, lon: np.ndarray) -> dict:
    """Mean |step| across 0.25 deg-aligned cell edges vs across all others."""
    on_b, off_b = [], []

    # west-east steps: edge j lies between columns j and j+1
    dx = np.abs(np.diff(arr, axis=1))
    lon_on = _edge_is_on_coarse_boundary(lon)
    on_b.append(dx[:, lon_on]); off_b.append(dx[:, ~lon_on])

    # south-north steps
    dy = np.abs(np.diff(arr, axis=0))
    lat_on = _edge_is_on_coarse_boundary(lat)
    on_b.append(dy[lat_on, :]); off_b.append(dy[~lat_on, :])

    on = np.concatenate([a[np.isfinite(a)].ravel() for a in on_b])
    off = np.concatenate([a[np.isfinite(a)].ravel() for a in off_b])
    on_mean, off_mean = float(np.mean(on)), float(np.mean(off))
    return {
        "on_boundary_mean_step": on_mean,
        "interior_mean_step": off_mean,
        "ratio": on_mean / off_mean if off_mean > 0 else float("nan"),
        "n_on": on.size,
        "n_off": off.size,
    }


def two_panel(before, after, lat, lon, *, cmap, units, label,
              title_before, title_after, outfile):
    """Before/after on one shared quantile scale, plus the after-minus-before
    difference on a diverging scale centred at zero."""
    pooled = np.concatenate([
        before[np.isfinite(before)].ravel(), after[np.isfinite(after)].ravel()
    ])
    norm = quantile_boundary_norm(pooled)

    diff = after - before
    finite_diff = diff[np.isfinite(diff)]
    lim = float(np.nanpercentile(np.abs(finite_diff), 99)) or 1.0
    diff_norm = TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim)

    fig, axes = plt.subplots(
        1, 3, figsize=(19, 5.5), subplot_kw={"projection": ccrs.PlateCarree()}
    )
    panels = [
        (before, title_before, cmap, norm, label, units),
        (after, title_after, cmap, norm, label, units),
        (diff, "after − before", "RdBu_r", diff_norm, f"Δ {label}", units),
    ]
    for ax, (data, title, cm, nm, lab, un) in zip(axes, panels):
        mesh = ax.pcolormesh(lon, lat, data, cmap=cm, norm=nm,
                             shading="auto", transform=ccrs.PlateCarree())
        ax.add_feature(cfeature.STATES, linewidth=0.4, edgecolor="0.3")
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()],
                      crs=ccrs.PlateCarree())
        ax.set_title(title, fontsize=11)
        cb = fig.colorbar(mesh, ax=ax, orientation="horizontal",
                          pad=0.05, shrink=0.9)
        cb.set_label(f"{lab} ({un})", fontsize=9)
        cb.ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {os.path.basename(outfile)}")


def main():
    report = []
    for prefix, label, units, cmap in [
        ("AnnualHarvest", "Annual wood harvest", "unitless", "OrRd"),
        ("Biomass", "Aboveground biomass (TOTVEGC_ABG)", "kgC/m^2", "viridis"),
    ]:
        old_path = os.path.join(OLD_OUT, f"{prefix}_{YEAR}.tif")
        new_path = os.path.join(NEW_OUT, f"{prefix}_{YEAR}.tif")
        if not (os.path.exists(old_path) and os.path.exists(new_path)):
            print(f"{prefix}: missing {old_path if not os.path.exists(old_path) else new_path}")
            continue

        before, lat, lon = read_tif(old_path)
        after, lat2, lon2 = read_tif(new_path)
        assert before.shape == after.shape, f"{prefix}: grid mismatch"
        assert np.allclose(lat, lat2) and np.allclose(lon, lon2), \
            f"{prefix}: coordinate mismatch between the two runs"

        b_before = blockiness_ratio(before, lat, lon)
        b_after = blockiness_ratio(after, lat, lon)
        report.append((prefix, b_before, b_after))

        print(f"\n{prefix} {YEAR}")
        print(f"  before  0.25deg-edge step={b_before['on_boundary_mean_step']:.5g}  "
              f"interior={b_before['interior_mean_step']:.5g}  "
              f"ratio={b_before['ratio']:.3f}")
        print(f"  after   0.25deg-edge step={b_after['on_boundary_mean_step']:.5g}  "
              f"interior={b_after['interior_mean_step']:.5g}  "
              f"ratio={b_after['ratio']:.3f}")

        two_panel(
            before, after, lat, lon,
            cmap=cmap, units=units, label=label,
            title_before=f"{label} {YEAR} — harvfix (blocky forcing)",
            title_after=f"{label} {YEAR} — harvfixsmooth",
            outfile=os.path.join(NEW_OUT, f"{prefix}BeforeAfter_{YEAR}.png"),
        )

    if report:
        txt = os.path.join(NEW_OUT, f"blockiness_metric_{YEAR}.txt")
        with open(txt, "w") as fh:
            fh.write(
                f"Blockiness of the {COARSE_DEG} deg grid in year {YEAR}.\n"
                "Mean |step| across cell edges that fall on a 0.25 deg boundary,\n"
                "divided by the mean |step| across all other cell edges.\n"
                "1.0 = no preferential jump at coarse boundaries.\n\n"
            )
            for prefix, b_before, b_after in report:
                fh.write(f"{prefix}\n")
                for name, b in (("before (harvfix)", b_before),
                                ("after  (harvfixsmooth)", b_after)):
                    fh.write(
                        f"  {name:26s} ratio={b['ratio']:.4f}  "
                        f"on-boundary={b['on_boundary_mean_step']:.6g}  "
                        f"interior={b['interior_mean_step']:.6g}  "
                        f"(n_on={b['n_on']}, n_off={b['n_off']})\n"
                    )
                fh.write("\n")
        print(f"\nWrote {txt}")


if __name__ == "__main__":
    main()
