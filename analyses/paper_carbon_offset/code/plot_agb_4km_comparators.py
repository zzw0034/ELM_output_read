"""
All fields on the ELM 4 km grid, same quantity (aboveground tree woody
carbon, Mg C/ha per land area), mean of the 17 ESA epochs 2005-2012,
2015-2023:

  (a) C  ELM 4 km run: tree-PFT (itype 1-8) stem C x wtgcell
  (b) ESA CCI v7.0 AGB x carbon fraction (default 0.50), area-weighted from
      0.01 deg to the 1/24 deg grid over land pixels
  (c) A  ELM 0.5 deg run copied to its 144 child 4 km cells (flat in a cell)
  (d) B  ELM 0.5 deg downscaled by 4 km land cover:
         B(i) = sum_t density_t(parent 0.5 deg cell) * frac_t(4 km cell i),
      computed per year, then averaged. density_t is the 0.5 deg stem C per
      unit area of tree type t; frac_t the 4 km type fraction. Where a 4 km
      type is absent from its parent, the parent's all-tree density is used
      (reported).

Prints common-support statistics against ESA at 4 km, and a preview of the
within-0.5 deg anomaly test (MANUSCRIPT_BLUEPRINT.md D6 step 3-4): anomalies
are deviations from the area-weighted mean of the same valid children in
each 0.5 deg cell; A has zero anomalies by construction. Coarse cells need
>= MIN_CHILDREN valid children. Results are shown with and without the
0.5 deg row 30.5-31.0 N that contains the 30.833 N daylength line. This is a
preview, not the final D6 evaluation.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/plot_agb_4km_comparators.py [--cf 0.50]
Inputs (pulled from proj-shared, git-ignored):
    _cache/obs_compare/elm4km_tree_stemc_bytype_2005-2023.npz
    _cache/obs_compare/elm0p5deg_tree_stemc_bytype_2005-2023.npz
    _cache/obs/ESACCI-...-fv7.0_SEUS_lat24-37.5_lon-95--74.nc
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
from plot_agb_elm4km_esa4km_elm0p5 import aggregate_esa_to_grid  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E4_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm4km_tree_stemc_bytype_2005-2023.npz")
E05_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm0p5deg_tree_stemc_bytype_2005-2023.npz")
OUT_DIR = os.path.join(ROOT, "figures/obs")
GC_M2_TO_MGC_HA = 0.01
N = 12              # 4 km cells per 0.5 deg cell along each axis
MIN_CHILDREN = 72   # of 144, for the within-cell preview
DAYL_ROW = (30.5, 31.0)


def to_children(coarse):
    """Repeat a (..., ny, nx) coarse field onto the (..., ny*N, nx*N) fine grid."""
    return np.repeat(np.repeat(coarse, N, axis=-2), N, axis=-1)


def block_sum(x):
    ny, nx = x.shape[0] // N, x.shape[1] // N
    return x.reshape(ny, N, nx, N).sum(axis=(1, 3))


def downscale_B(e4, e05):
    """Per-year land-cover-downscaled 0.5 deg field on the 4 km grid, then the
    multi-year mean. Returns (B mean in gC/m2, fallback area share)."""
    fb_area, tot_area, out = 0.0, 0.0, []
    w4 = e4["area"] * e4["landfrac"]
    for k in range(e4["year"].size):
        dens05 = e05["stemc_dens_by_type"][k]              # (type, 27, 42)
        tree05 = e05["tree_stemc"][k] / e05["tree_frac"][k]  # all-tree density
        frac4 = np.nan_to_num(e4["frac_by_type"][k])        # (type, 324, 504)
        dens_c = to_children(dens05)
        miss = (frac4 > 0) & ~np.isfinite(dens_c)
        dens_c = np.where(miss, to_children(tree05)[None], dens_c)
        b = np.nansum(np.nan_to_num(dens_c) * frac4, axis=0)
        b = np.where(np.isfinite(e4["tree_stemc"][k]), b, np.nan)
        out.append(b)
        fb_area += np.nansum((frac4 * miss).sum(axis=0) * w4)
        tot_area += np.nansum(frac4.sum(axis=0) * w4)
    return np.mean(out, axis=0), fb_area / tot_area


def stats_vs(obs, model, w, label):
    ok = np.isfinite(obs) & np.isfinite(model) & (w > 0)
    mo, mm = np.average(obs[ok], weights=w[ok]), np.average(model[ok], weights=w[ok])
    rmse = np.sqrt(np.average((model[ok] - obs[ok]) ** 2, weights=w[ok]))
    r = np.corrcoef(model[ok], obs[ok])[0, 1]
    print(f"  {label:<34s} mean {mm:5.1f} vs ESA {mo:5.1f}  bias {mm - mo:+5.1f}  RMSE {rmse:5.1f}  r {r:.2f}")


def within_cell(fields, w, lat4, exclude_dayl):
    """fields: dict name -> 4 km field (ESA first). Prints anomaly skill."""
    valid = (w > 0)
    for f in fields.values():
        valid &= np.isfinite(f)
    nvalid = block_sum(valid.astype(int))
    elig_c = nvalid >= MIN_CHILDREN
    if exclude_dayl:
        lat05 = lat4.reshape(-1, N).mean(axis=1)
        elig_c &= ~((lat05 > DAYL_ROW[0]) & (lat05 < DAYL_ROW[1]))[:, None]
    elig = valid & to_children(elig_c)
    wv = np.where(elig, w, 0.0)
    anoms = {}
    for name, f in fields.items():
        fz = np.where(elig, f, 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            cm = block_sum(fz * wv) / block_sum(wv)
        anoms[name] = np.where(elig, f - to_children(cm), np.nan)
    o = anoms.pop("ESA")
    ok = elig
    so = np.sqrt(np.average(o[ok] ** 2, weights=wv[ok]))
    tag = "excluding 30.5-31.0N row" if exclude_dayl else "all eligible cells"
    print(f"  [{tag}] coarse cells {int(elig_c.sum())}, fine cells {int(ok.sum())}; "
          f"ESA anomaly SD {so:.1f} MgC/ha")
    print(f"    {'A 0.5 deg copied (flat)':<30s} r   n/a  SS  0.00  SD ratio 0.00")
    for name, m in anoms.items():
        r = np.corrcoef(m[ok], o[ok])[0, 1]
        ss = 1 - np.average((m[ok] - o[ok]) ** 2, weights=wv[ok]) / np.average(o[ok] ** 2, weights=wv[ok])
        sd = np.sqrt(np.average(m[ok] ** 2, weights=wv[ok])) / so
        print(f"    {name:<30s} r {r:5.2f}  SS {ss:5.2f}  SD ratio {sd:4.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cf", type=float, default=0.50, help="carbon fraction of dry AGB")
    cf = ap.parse_args().cf

    e4, e05 = np.load(E4_NPZ), np.load(E05_NPZ)
    years = e4["year"].tolist()
    assert years == e05["year"].tolist()
    lat4, lon4 = e4["lat"], e4["lon"]
    assert lat4.size == N * e05["lat"].size and lon4.size == N * e05["lon"].size
    assert np.allclose(lat4.reshape(-1, N).mean(axis=1), e05["lat"], atol=1e-4)
    assert np.allclose(lon4.reshape(-1, N).mean(axis=1), e05["lon"], atol=1e-4)
    w4 = e4["area"] * e4["landfrac"]
    w4 = np.where(np.isfinite(w4), w4, 0.0)

    C = np.nanmean(e4["tree_stemc"], axis=0) * GC_M2_TO_MGC_HA
    A = np.where(np.isfinite(C), to_children(np.nanmean(e05["tree_stemc"], axis=0)), np.nan) * GC_M2_TO_MGC_HA
    B, fb = downscale_B(e4, e05)
    B = B * GC_M2_TO_MGC_HA

    esa = xr.open_dataset(ESA_NC, decode_times=False)
    esa_years = np.array([(datetime.date(1990, 1, 1) + datetime.timedelta(days=float(t))).year
                          for t in esa["time"].values])
    idx = np.where(np.isin(esa_years, years))[0]
    assert sorted(esa_years[idx].tolist()) == sorted(years)
    esa_c = esa["agb"].isel(time=idx).astype("float32").mean("time").values[::-1, :] * cf
    lat_f, lon_f = esa["lat"].values[::-1], esa["lon"].values
    lon2d, lat2d = np.meshgrid(lon_f, lat_f)
    O, _ = aggregate_esa_to_grid(esa_c, lat_f, lon_f, land_mask(lon2d, lat2d), lat4, lon4)
    O = np.where(np.isfinite(C), O, np.nan)

    # Conservation check: B and A should reproduce the 0.5 deg run when
    # averaged back over each coarse cell.
    okw = np.where(np.isfinite(B), w4, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        b_back = block_sum(np.nan_to_num(B) * okw) / block_sum(okw)
    e05m = np.nanmean(e05["tree_stemc"], axis=0) * GC_M2_TO_MGC_HA
    d = (b_back - e05m)[np.isfinite(b_back) & np.isfinite(e05m)]
    print(f"epochs ({len(years)}), carbon fraction {cf}")
    print(f"B check: block mean of B minus native 0.5 deg: mean {d.mean():+.2f}, max |d| {np.abs(d).max():.2f} MgC/ha; "
          f"fallback density used on {fb * 100:.2f}% of tree area")

    print("Common support on 4 km cells (vs ESA aggregated to 4 km):")
    for name, f in [("C  ELM 4 km", C), ("A  ELM 0.5 deg copied", A), ("B  ELM 0.5 deg downscaled", B)]:
        stats_vs(O, f, w4, name)
    print(f"Within-0.5 deg anomaly preview (>= {MIN_CHILDREN}/144 valid children):")
    for excl in (False, True):
        within_cell({"ESA": O, "B 0.5 deg downscaled": B, "C ELM 4 km": C}, w4, lat4, excl)

    vmax = float(np.ceil(np.nanpercentile(np.concatenate([C.ravel(), O.ravel(), A.ravel(), B.ravel()]), 99.5)
                         / 20) * 20)
    levels = np.linspace(0, vmax, 17)
    cmap = plt.get_cmap("Greens", len(levels))
    cmap.set_bad(BAD)
    norm = BoundaryNorm(levels, ncolors=cmap.N, extend="max")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.6), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.subplots_adjust(wspace=0.12, hspace=0.18)
    panels = [(C, "(a) ELM 4 km run"),
              (O, f"(b) ESA CCI v7.0 AGB × {cf:.2f}, aggregated to 4 km"),
              (A, "(c) ELM 0.5° run, copied to 4 km"),
              (B, "(d) ELM 0.5° run, downscaled by 4 km tree-PFT fractions")]
    for ax, (f, title) in zip(axes.ravel(), panels):
        mesh = draw(ax, lon4, lat4, f, cmap, norm, title)
    fig.suptitle(f"Aboveground tree woody carbon on the 4 km grid, mean of {len(years)} years "
                 f"{min(years)}–{max(years)} (no 2013–2014)", x=0.06, y=0.97, ha="left", fontsize=13)
    cb = fig.colorbar(mesh, ax=axes, orientation="horizontal", pad=0.07, shrink=0.55, aspect=45)
    cb.set_label("Mg C ha$^{-1}$")
    cb.ax.text(0.0, -3.9, "ELM: (LIVESTEMC + DEADSTEMC) of tree PFTs × PFT area fraction, per land area. "
               "(d): Σ_t density_t(0.5°) × fraction_t(4 km).\nESA: land pixels only, area-weighted to the "
               "ELM 1/24° grid. All panels masked where ELM 4 km has no vegetation.",
               transform=cb.ax.transAxes, fontsize=8, color="#555555", va="top")
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"agb_4km_comparators_{min(years)}-{max(years)}_cf{int(round(cf * 100)):02d}.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
