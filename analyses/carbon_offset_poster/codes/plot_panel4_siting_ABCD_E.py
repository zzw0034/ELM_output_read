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
from common import (FOURKM, SEC_PER_YEAR_NOLEAP, year_of, area_weights,
                     day_weighted_annual_mean)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSTER_DIR = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(POSTER_DIR, "outputs")

Y0, Y1 = 2091, 2100
CASES = FOURKM
MANAGED, POTENTIAL_LABEL = "SSP3-7.0 RF", "Reforestation offset (RF - Default)"

# 2026-09-17: paper_carbon_offset/common.py's FOURKM_SUBDIR="" + CASE_ROOT
# (/scratch/hpcl-cli185/zw5/cime_output_dirs) is stale for these 4km future
# cases -- confirmed gone from scratch (moved/cleaned since the 2026-09-15
# fig05 run that last used it successfully). The durable copy lives here
# instead (same location already used by extract_biomass_soc.py for the
# 4km historical case), verified to have complete h0 output through 2100
# for both "SSP3-7.0" and "SSP3-7.0 RF". Do not confuse with the *separate*
# 20260917-dated case dirs under e3sm_cases/ (a concurrent, unrelated
# rerun in progress today per this session's own memory note -- different
# case-name prefix, no overlap with what's read here).
FOURKM_RUN_ROOT = "/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260901_before_seus_rerun"


def case_run_dir(case):
    return os.path.join(FOURKM_RUN_ROOT, case, "run")


def h0_files_here(case):
    import glob
    d = case_run_dir(case)
    return sorted(glob.glob(os.path.join(d, f"{case}.elm.h0.*.nc")))


def load_mean_map_here(case, var, y0, y1):
    files = [f for f in h0_files_here(case) if y0 <= year_of(f) <= y1]
    if not files:
        raise ValueError(f"no h0 files for {case} in [{y0},{y1}] under {case_run_dir(case)}")
    stack, lat, lon = [], None, None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        vals = day_weighted_annual_mean(ds[var], tb)
        if ds[var].attrs.get("units", "").strip() == "gC/m^2/s":
            vals = vals * SEC_PER_YEAR_NOLEAP
        stack.append(vals)
        if lat is None:
            lat, lon = ds["lat"].values, ds["lon"].values
        ds.close()
    return lon, lat, np.nanmean(np.stack(stack, axis=0), axis=0)


def load_year_stack(case, var, y0, y1):
    """Per-year maps (not the decadal mean) -- needed for interannual CV."""
    files = [f for f in h0_files_here(case) if y0 <= year_of(f) <= y1]
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
    lon, lat, ec_def = load_mean_map_here(CASES["SSP3-7.0"], "TOTECOSYSC", Y0, Y1)
    _, _, ec_man = load_mean_map_here(CASES[MANAGED], "TOTECOSYSC", Y0, Y1)
    potential = ec_man - ec_def

    print("  loading vulnerability maps ...")
    _, _, fire_loss = load_mean_map_here(risk_case, "PFT_FIRE_CLOSS", Y0, Y1)
    _, _, ec_risk = load_mean_map_here(risk_case, "TOTECOSYSC", Y0, Y1)
    _, _, btran = load_mean_map_here(risk_case, "BTRAN", Y0, Y1)
    ec_stack = load_year_stack(risk_case, "TOTECOSYSC", Y0, Y1)

    ds0 = xr.open_dataset(h0_files_here(CASES["SSP3-7.0"])[0], decode_times=False)
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
    # 2026-09-18 (user request): D had no colorbar (just an in-axes legend),
    # so it rendered visibly larger than A/B/C once fig.colorbar(ax=...)
    # shrank each of THEIR map axes to make room for a colorbar beneath it.
    # Fix: an explicit GridSpec with a dedicated, fixed-height colorbar row
    # under EVERY map (including D's, left blank) -- all four map axes then
    # get an identical cell size regardless of what's drawn below them.
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.gridspec import GridSpec

    fig = plt.figure(figsize=(13, 12.5))
    gs = GridSpec(4, 2, figure=fig, height_ratios=[10, 1, 10, 1], hspace=0.35, wspace=0.15)
    map_slots = {"A": gs[0, 0], "B": gs[0, 1], "C": gs[2, 0], "D": gs[2, 1]}
    cbar_slots = {"A": gs[1, 0], "B": gs[1, 1], "C": gs[3, 0]}  # D's [3, 1] stays blank

    specs = [
        ("A", potential, f"A. {POTENTIAL_LABEL}\n2091-2100 (gC m$^{{-2}}$)", "YlGn"),
        ("B", fire_pct, "B. Fire risk: annual fire C loss\nas % of standing stock", "OrRd"),
        ("C", vuln, "C. Composite vulnerability\n(fire + drought + interannual CV, rank-normalised)", "magma_r"),
    ]
    for key, field, title, cmap in specs:
        ax = fig.add_subplot(map_slots[key], projection=ccrs.PlateCarree())
        make_axes(ax)
        vmax = np.nanpercentile(field[land], 99)
        vmin = np.nanpercentile(field[land], 1)
        pc = ax.pcolormesh(lon, lat, field, transform=ccrs.PlateCarree(),
                           cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
        ax.set_title(title, fontsize=10)
        cax = fig.add_subplot(cbar_slots[key])
        cb = fig.colorbar(pc, cax=cax, orientation="horizontal")
        cb.ax.tick_params(labelsize=8)

    ax = fig.add_subplot(map_slots["D"], projection=ccrs.PlateCarree())
    make_axes(ax)
    ax.pcolormesh(lon, lat, quad, transform=ccrs.PlateCarree(),
                  cmap=ListedColormap(qcolors), norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4),
                  shading="auto")
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c) for c in qcolors]
    ax.legend(handles, qlabels, fontsize=7.5, loc="lower left", ncol=2)
    ax.set_title("D. Siting quadrants\n(split at area-weighted medians)", fontsize=10)

    # 2026-09-18 (user request): no figure-level suptitle. Kept the
    # "A./B./C./D." panel titles -- the poster caption/bullets reference
    # panels by letter.
    out_abcd = os.path.join(OUT_DIR, "panel4_siting_RF_4km_ABCD.png")
    fig.savefig(out_abcd, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Figure written to {out_abcd}")

    # Sanity-check numbers against the original fig05 run's printed output
    # (thresholds 2940 gC/m2 / 0.494, shares 33.6/16.4/16.4/33.6%) -- same
    # case, same year window, only the data path changed, so these should
    # match closely if the proj-shared copy really is the same underlying
    # run output.
    print(f"\nthresholds: potential median {p_med:.0f} gC/m2, vulnerability median {v_med:.3f}")
    for q, lab in enumerate(qlabels):
        m = land & (quad == q)
        share = 100 * np.nansum(w[m]) / np.nansum(w[land])
        mean_p = np.nansum(potential[m] * w[m]) / np.nansum(w[m]) if m.sum() else np.nan
        print(f"  {lab.replace(chr(10),' '):28s} {share:5.1f}%  mean potential {mean_p:7.0f} gC/m2")

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
