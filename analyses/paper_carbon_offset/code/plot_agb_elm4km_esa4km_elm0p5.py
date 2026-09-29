"""
Three-way map of the same aboveground tree woody carbon quantity:
ELM 4 km | ESA CCI v7.0 aggregated to the ELM 4 km grid | ELM 0.5 deg,
each the mean of the 17 ESA epochs inside the transient (2005-2012,
2015-2023).

ELM: tree-PFT (itype 1-8) LIVESTEMC + DEADSTEMC x wtgcell per gridcell land
area (extract_elm_4km_tree_stemc.py, run for both resolutions).
ESA: dry AGB x carbon fraction (default 0.50, decided 2026-09-29;
--cf overrides), aggregated from its 0.01 deg grid to the 1/24 deg ELM grid
with exact area-overlap weights, averaging land pixels only (ocean is
stored as 0 in the file and is excluded with the Natural Earth display
mask), so it too is per unit land area. Cells where ELM 4 km has no
vegetation are masked.

Also prints first-look statistics on common support (4 km cells, and 0.5 deg
cells from area-weighted block means). These are previews, not the D6
Figure 1 evaluation (no final mask rules, no 30.833N exclusion).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \
        code/plot_agb_elm4km_esa4km_elm0p5.py [--cf 0.50]
"""
import argparse
import datetime
import os
import sys

import cartopy.crs as ccrs
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import BoundaryNorm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_obs_esacci_agb_v7_mean import NC as ESA_NC, land_mask  # noqa: E402
from plot_elm_vs_esacci_agb import BAD, draw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELM4_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm4km_tree_stemc_2005-2023.npz")
ELM05_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm0p5deg_tree_stemc_2005-2023.npz")
OUT_DIR = os.path.join(ROOT, "figures/obs")
GC_M2_TO_MGC_HA = 0.01
BLOCK = 12  # 4 km cells per 0.5 deg cell along each axis


def edges_from_centers(c):
    d = np.diff(c).mean()
    return np.concatenate([c - d / 2, [c[-1] + d / 2]])


def overlap_matrix(coarse_edges, fine_edges):
    """1-D overlap length of each fine interval with each coarse interval,
    shape (n_coarse, n_fine). Both edge arrays ascending."""
    lo = np.maximum(coarse_edges[:-1, None], fine_edges[None, :-1])
    hi = np.minimum(coarse_edges[1:, None], fine_edges[None, 1:])
    return np.clip(hi - lo, 0.0, None)


def aggregate_esa_to_grid(esa_c, lat_f, lon_f, is_land, lat_c, lon_c):
    """Area-weighted mean of land pixels of esa_c (fine, lat ascending) on the
    coarse grid given by centres lat_c, lon_c. Returns (mean, land share)."""
    wy = overlap_matrix(edges_from_centers(lat_c), edges_from_centers(lat_f)) * np.cos(np.deg2rad(lat_f))[None, :]
    wx = overlap_matrix(edges_from_centers(lon_c), edges_from_centers(lon_f))
    m = is_land.astype("f8")
    num = wy @ (np.where(is_land, esa_c, 0.0)) @ wx.T
    den = wy @ m @ wx.T
    tot = wy @ np.ones_like(m) @ wx.T
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan), den / tot


def block_mean(field, weight, n=BLOCK):
    ok = np.isfinite(field) & (weight > 0)
    f = np.where(ok, field, 0.0)
    w = np.where(ok, weight, 0.0)
    ny, nx = field.shape[0] // n, field.shape[1] // n
    num = (f * w).reshape(ny, n, nx, n).sum(axis=(1, 3))
    den = w.reshape(ny, n, nx, n).sum(axis=(1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan), den


def compare(a, b, w, label):
    ok = np.isfinite(a) & np.isfinite(b) & (w > 0)
    wa = np.average(a[ok], weights=w[ok])
    wb = np.average(b[ok], weights=w[ok])
    r = np.corrcoef(a[ok], b[ok])[0, 1]
    rmse = np.sqrt(np.average((a[ok] - b[ok]) ** 2, weights=w[ok]))
    print(f"  {label}: n={ok.sum()} mean {wa:.1f} vs {wb:.1f} MgC/ha, bias {wa - wb:+.1f}, "
          f"RMSE {rmse:.1f}, r {r:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cf", type=float, default=0.50, help="carbon fraction of dry AGB")
    cf = ap.parse_args().cf

    e4 = np.load(ELM4_NPZ)
    e05 = np.load(ELM05_NPZ)
    years = e4["year"].tolist()
    assert years == e05["year"].tolist(), "4 km and 0.5 deg extracts cover different years"
    elm4 = np.nanmean(e4["tree_stemc"], axis=0) * GC_M2_TO_MGC_HA
    elm05 = np.nanmean(e05["tree_stemc"], axis=0) * GC_M2_TO_MGC_HA
    lat4, lon4, lat05, lon05 = e4["lat"], e4["lon"], e05["lat"], e05["lon"]
    assert np.all(np.diff(lat4) > 0) and np.all(np.diff(lat05) > 0)
    w4 = e4["area"] * e4["landfrac"]

    esa = xr.open_dataset(ESA_NC, decode_times=False)
    esa_years = np.array([(datetime.date(1990, 1, 1) + datetime.timedelta(days=float(t))).year
                          for t in esa["time"].values])
    idx = np.where(np.isin(esa_years, years))[0]
    assert sorted(esa_years[idx].tolist()) == sorted(years)
    esa_c = esa["agb"].isel(time=idx).astype("float32").mean("time").values * cf
    lat_f, lon_f = esa["lat"].values[::-1], esa["lon"].values
    esa_c = esa_c[::-1, :]
    lon2d, lat2d = np.meshgrid(lon_f, lat_f)
    is_land = land_mask(lon2d, lat2d)
    esa4, land_share = aggregate_esa_to_grid(esa_c, lat_f, lon_f, is_land, lat4, lon4)
    esa4 = np.where(np.isfinite(elm4), esa4, np.nan)

    print(f"epochs ({len(years)}): {' '.join(map(str, years))}; carbon fraction {cf}")
    print("First-look statistics (not the D6 evaluation):")
    compare(elm4, esa4, w4, "4 km cells, ELM 4 km vs ESA->4 km")
    elm4_05, wb = block_mean(elm4, w4)
    esa_05, _ = block_mean(esa4, w4)
    compare(elm4_05, esa_05, wb, "0.5 deg, ELM 4 km aggregated vs ESA aggregated")
    compare(elm05, esa_05, wb, "0.5 deg, ELM 0.5 deg native vs ESA aggregated")
    compare(elm05, elm4_05, wb, "0.5 deg, ELM 0.5 deg native vs ELM 4 km aggregated")

    vmax = float(np.ceil(np.nanpercentile(np.concatenate([elm4.ravel(), esa4.ravel(), elm05.ravel()]), 99.5)
                         / 20) * 20)
    levels = np.linspace(0, vmax, 17)
    cmap = plt.get_cmap("Greens", len(levels))
    cmap.set_bad(BAD)
    norm = BoundaryNorm(levels, ncolors=cmap.N, extend="max")

    fig, axes = plt.subplots(1, 3, figsize=(21, 4.9), subplot_kw={"projection": ccrs.PlateCarree()})
    draw(axes[0], lon4, lat4, elm4, cmap, norm, "(a) ELM 4 km: tree-PFT stem C")
    draw(axes[1], lon4, lat4, esa4, cmap, norm, f"(b) ESA CCI v7.0 AGB × {cf}, aggregated to 4 km")
    mesh = draw(axes[2], lon05, lat05, elm05, cmap, norm, "(c) ELM 0.5°: tree-PFT stem C")
    span = f"{min(years)}–{max(years)}"
    fig.suptitle(f"Aboveground tree woody carbon, mean of the same {len(years)} years {span} (no 2013–2014)",
                 x=0.04, y=1.02, ha="left", fontsize=13)
    cb = fig.colorbar(mesh, ax=axes, orientation="horizontal", pad=0.13, shrink=0.45, aspect=45)
    cb.set_label("Mg C ha$^{-1}$")
    cb.ax.text(0.0, -3.9, "ELM: (LIVESTEMC + DEADSTEMC) of tree PFTs × PFT area fraction, per land area.\n"
               "ESA: land pixels only, area-weighted to the ELM 1/24° grid; masked where ELM 4 km has no "
               "vegetation. Grey = ocean/lakes.", transform=cb.ax.transAxes, fontsize=8, color="#555555",
               va="top")
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = f"cf{int(round(cf * 100)):02d}"
    out = os.path.join(OUT_DIR, f"agb_elm4km_esa4km_elm0p5_{min(years)}-{max(years)}_{tag}.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
