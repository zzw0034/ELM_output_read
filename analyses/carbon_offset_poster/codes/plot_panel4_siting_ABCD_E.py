"""
Poster Panel 4: siting map (A-D, 2x2) and the potential-vs-vulnerability
scatter (E, standalone). Same data and math as
../../paper_carbon_offset/fig05_siting_potential_vs_vulnerability.py --
this script reuses that project's common.py (case names, area weights,
day-weighted annual means) via sys.path rather than re-deriving them, per
paper_carbon_offset/common.py's own "deliberately copied rather than
imported... across per-case-family folders" caution: that caution is about
NOT importing between the 20260910_seus_rerun / 20260908_seus_4km per-case
folders, a different pair from this one. carbon_offset_poster reusing
paper_carbon_offset's *own* common.py is the same "reuse, do not fork"
relationship already documented in this project's README.

Differences from fig05_siting_potential_vs_vulnerability.py:
  - Output is split: a 2x2 figure (A potential map, B fire risk map,
    C composite vulnerability map, D siting quadrants map) with a
    shorter, poster-facing title, and a SEPARATE standalone figure for
    E (the potential-vs-vulnerability scatter). F (the area-share bar
    chart) is dropped -- not requested for this poster panel.
  - Fixed to RF (reforestation) and 4 km only (the poster's chosen
    resolution/scenario for Panel 4); no CLI args.

Runs on Pathfinder via Slurm (submit_py.sbatch) -- reads TOTECOSYSC (2
cases), PFT_FIRE_CLOSS, BTRAN, and a 10-year TOTECOSYSC stack for CV, all
at 4 km (324x504). Comparable cost to the poster's other 4km extractions
(~1-2 min), much cheaper than a full multi-scenario NBP reload.
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "paper_carbon_offset"))
from common import (FOURKM, FOURKM_SUBDIR, SEC_PER_YEAR_NOLEAP, h0_files,
                     year_of, area_weights, day_weighted_annual_mean, load_mean_map)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSTER_DIR = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(POSTER_DIR, "outputs")

Y0, Y1 = 2091, 2100
CASES, SUBDIR = FOURKM, FOURKM_SUBDIR
MANAGED, POTENTIAL_LABEL = "SSP3-7.0 RF", "Reforestation offset (RF - Default)"


def load_year_stack(case, var, y0, y1, subdir):
    """Per-year maps (not the decadal mean) -- needed for interannual CV."""
    files = [f for f in h0_files(case, subdir) if y0 <= year_of(f) <= y1]
    stack = []
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        vals = day_weighted_annual_mean(ds[var], tb)
        if ds[var].attrs.get("units", "").strip() == "gC/m^2/s":
            vals = vals * SEC_PER_YEAR_NOLEAP
        stack.append(vals)
        ds.close()
    return np.stack(stack, axis=0)


def make_axes(ax):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def wmedian(vals, w):
    """Area-weighted median."""
    m = np.isfinite(vals) & (w > 0)
    v, ww = vals[m], w[m]
    order = np.argsort(v)
    v, ww = v[order], ww[order]
    c = np.cumsum(ww) / np.sum(ww)
    return float(v[np.searchsorted(c, 0.5)])


def rank_norm(field, land):
    """Percentile rank in [0,1] over land cells only (outlier-robust,
    unit-free -- see paper_carbon_offset/fig05... for the full rationale)."""
    out = np.full(field.shape, np.nan)
    v = field[land]
    good = np.isfinite(v)
    r = np.full(v.shape, np.nan)
    order = np.argsort(v[good])
    ranks = np.empty(order.shape)
    ranks[order] = np.arange(order.size)
    r[good] = ranks / max(order.size - 1, 1)
    out[land] = r
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    risk_case = CASES[MANAGED]

    print("  loading offset maps ...")
    lon, lat, ec_def = load_mean_map(CASES["SSP3-7.0"], "TOTECOSYSC", Y0, Y1, subdir=SUBDIR)
    _, _, ec_man = load_mean_map(CASES[MANAGED], "TOTECOSYSC", Y0, Y1, subdir=SUBDIR)
    potential = ec_man - ec_def

    print("  loading vulnerability maps ...")
    _, _, fire_loss = load_mean_map(risk_case, "PFT_FIRE_CLOSS", Y0, Y1, subdir=SUBDIR)
    _, _, ec_risk = load_mean_map(risk_case, "TOTECOSYSC", Y0, Y1, subdir=SUBDIR)
    _, _, btran = load_mean_map(risk_case, "BTRAN", Y0, Y1, subdir=SUBDIR)
    ec_stack = load_year_stack(risk_case, "TOTECOSYSC", Y0, Y1, SUBDIR)

    ds0 = xr.open_dataset(h0_files(CASES["SSP3-7.0"], SUBDIR)[0], decode_times=False)
    w = area_weights(ds0)
    ds0.close()
    land = w > 0

    with np.errstate(divide="ignore", invalid="ignore"):
        fire_pct = 100.0 * fire_loss / ec_risk
        drought = 1.0 - btran
        cv = 100.0 * np.nanstd(ec_stack, axis=0) / np.nanmean(ec_stack, axis=0)

    vuln = np.nanmean(np.stack([rank_norm(fire_pct, land), rank_norm(drought, land),
                                rank_norm(cv, land)], axis=0), axis=0)

    p_med, v_med = wmedian(potential, w), wmedian(vuln, w)
    quad = np.full(potential.shape, np.nan)
    hi_p, lo_v = potential >= p_med, vuln < v_med
    quad[land & hi_p & lo_v] = 3
    quad[land & hi_p & ~lo_v] = 2
    quad[land & ~hi_p & lo_v] = 1
    quad[land & ~hi_p & ~lo_v] = 0

    qcolors = ["#d9d9d9", "#9ecae1", "#fdae6b", "#238b45"]
    qlabels = ["low potential,\nhigh risk", "low potential,\nlow risk",
               "high potential,\nhigh risk", "HIGH potential,\nLOW risk"]

    # ------------------------------------------------------- 2x2: A, B, C, D
    fig = plt.figure(figsize=(13, 12))
    specs = [
        (1, potential, f"A. {POTENTIAL_LABEL}\n2091-2100 (gC m$^{{-2}}$)", "YlGn"),
        (2, fire_pct, "B. Fire risk: annual fire C loss\nas % of standing stock", "OrRd"),
        (3, vuln, "C. Composite vulnerability\n(fire + drought + interannual CV, rank-normalised)", "magma_r"),
    ]
    for pos, field, title, cmap in specs:
        ax = fig.add_subplot(2, 2, pos, projection=ccrs.PlateCarree())
        make_axes(ax)
        vmax = np.nanpercentile(field[land], 99)
        vmin = np.nanpercentile(field[land], 1)
        pc = ax.pcolormesh(lon, lat, field, transform=ccrs.PlateCarree(),
                           cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
        cb = fig.colorbar(pc, ax=ax, orientation="horizontal", pad=0.05, shrink=0.85)
        cb.ax.tick_params(labelsize=8)
        ax.set_title(title, fontsize=10)

    from matplotlib.colors import ListedColormap, BoundaryNorm
    ax = fig.add_subplot(2, 2, 4, projection=ccrs.PlateCarree())
    make_axes(ax)
    ax.pcolormesh(lon, lat, quad, transform=ccrs.PlateCarree(),
                  cmap=ListedColormap(qcolors), norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4),
                  shading="auto")
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c) for c in qcolors]
    ax.legend(handles, qlabels, fontsize=7.5, loc="lower left", ncol=2)
    ax.set_title("D. Siting quadrants\n(split at area-weighted medians)", fontsize=10)

    fig.suptitle("SEUS 4km SSP3-7.0: where to site carbon-offset projects (Reforestation)\n"
                 "vulnerability scored in the post-intervention run, not in Default",
                 fontsize=13)
    fig.tight_layout()
    out_abcd = os.path.join(OUT_DIR, "panel4_siting_RF_4km_ABCD.png")
    fig.savefig(out_abcd, dpi=150)
    plt.close(fig)
    print(f"Figure written to {out_abcd}")

    # ------------------------------------------------------------- E: scatter
    figE, axE = plt.subplots(figsize=(8, 7))
    pv, vv, wv, qv = potential[land], vuln[land], w[land], quad[land]
    good = np.isfinite(pv) & np.isfinite(vv)
    axE.scatter(pv[good], vv[good], s=np.clip(wv[good] / np.nanmax(wv) * 18, 1, 18),
                c=[qcolors[int(q)] for q in qv[good]], alpha=0.7, linewidths=0)
    axE.axvline(p_med, color="k", lw=0.8, ls="--")
    axE.axhline(v_med, color="k", lw=0.8, ls="--")
    axE.set_xlabel(f"{POTENTIAL_LABEL} (gC m$^{{-2}}$)", fontsize=11)
    axE.set_ylabel("Composite vulnerability (0-1)", fontsize=11)
    axE.set_title("Potential vs vulnerability\n(point size = gridcell land area)", fontsize=13)
    axE.grid(alpha=0.3)
    figE.tight_layout()
    out_e = os.path.join(OUT_DIR, "panel4_siting_RF_4km_E_scatter.png")
    figE.savefig(out_e, dpi=150)
    plt.close(figE)
    print(f"Figure written to {out_e}")


if __name__ == "__main__":
    main()
