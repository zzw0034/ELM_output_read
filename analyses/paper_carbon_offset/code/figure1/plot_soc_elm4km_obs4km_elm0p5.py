"""
Soil organic carbon maps, one figure per observation product:
rows = depth (0-30 cm, 0-100 cm); columns = ELM 4 km | observation on the
ELM 4 km grid | ELM 0.5 deg. ELM is the mean of the annual means 2000-2023.

Observation: HWSD v1.2 (3 arc-minute source, so remapped, not aggregated) or
SoilGrids 2.0 (WCS request on the ELM grid); see analysis_process_notes.md
section 3.4. Observations are masked where ELM 4 km has no soil column, so
all three panels share the same land/soil support.

Statistics printed per row (area x landfrac weights, valid common support;
first-look numbers, not the D6 evaluation):
  4 km cells: ELM 4 km vs observation
  0.5 deg cells (12 x 12 block means): ELM 4 km aggregated vs observation
    aggregated; ELM 0.5 deg native vs observation aggregated.

Runs locally (cartopy venv), from the analysis root, after pulling the inputs
into _cache/ (see the notes):
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \
        code/figure1/plot_soc_elm4km_obs4km_elm0p5.py [hwsd] [soilgrids]
"""
import os
import sys

import cartopy.crs as ccrs
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
from matplotlib.colors import BoundaryNorm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_agb_elm4km_esa4km_elm0p5 import BLOCK, block_mean  # noqa: E402
from plot_elm_vs_esacci_agb import draw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root
OBS = {
    "hwsd": ("HWSD v1.2", os.path.join(ROOT, "_cache/obs_soc/SOC_hwsd_SEUS_1_24deg.nc"),
             "HWSD v1.2 (0.05° source, remapped to 4 km)"),
    "soilgrids": ("SoilGrids 2.0", os.path.join(ROOT, "_cache/obs_soc/SOC_soilgrids_SEUS_1_24deg.nc"),
                  "SoilGrids 2.0 (WCS, on the 4 km grid)"),
}
ELM4_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm4km_soc_2000-2023.npz")
ELM05_NPZ = os.path.join(ROOT, "_cache/obs_compare/elm0p5deg_soc_2000-2023.npz")
OUT_DIR = os.path.join(ROOT, "figures/figure1")
DEPTHS = [("0_30", "0–30 cm", 2.0), ("0_100", "0–100 cm", 5.0)]  # key, label, colour-scale rounding (kg C m-2)


def stats(a, b, w):
    ok = np.isfinite(a) & np.isfinite(b) & (w > 0)
    wa, wb = np.average(a[ok], weights=w[ok]), np.average(b[ok], weights=w[ok])
    da, db = a[ok] - wa, b[ok] - wb
    r = np.average(da * db, weights=w[ok]) / np.sqrt(np.average(da ** 2, weights=w[ok]) * np.average(db ** 2, weights=w[ok]))
    return {"n": int(ok.sum()), "mean_a": wa, "mean_b": wb, "bias": wa - wb,
            "rmse": float(np.sqrt(np.average((a[ok] - b[ok]) ** 2, weights=w[ok]))), "r": float(r)}


def fmt(s):
    return f"bias {s['bias']:+.1f}, RMSE {s['rmse']:.1f}, r {s['r']:.2f}"


def main():
    which = sys.argv[1:] or list(OBS)
    e4, e05 = np.load(ELM4_NPZ), np.load(ELM05_NPZ)
    years = e4["year"].tolist()
    assert years == e05["year"].tolist() == list(range(2000, 2024)), "ELM extracts must both cover 2000-2023"
    lat4, lon4, lat05, lon05 = e4["lat"], e4["lon"], e05["lat"], e05["lon"]
    w4 = e4["area"] * e4["landfrac"]
    assert np.all(np.diff(lat4) > 0) and np.all(np.diff(lat05) > 0)
    assert np.allclose(lat4.reshape(-1, BLOCK).mean(axis=1), lat05) and np.allclose(lon4.reshape(-1, BLOCK).mean(axis=1), lon05), \
        "0.5 deg grid is not the 12 x 12 block grid of the 4 km grid"
    elm4 = {k: e4[f"soc_{k}_mean"].astype("f8") for k, _, _ in DEPTHS}
    elm05 = {k: e05[f"soc_{k}_mean"].astype("f8") for k, _, _ in DEPTHS}
    os.makedirs(OUT_DIR, exist_ok=True)

    for name in which:
        short, path, obs_title = OBS[name]
        with netCDF4.Dataset(path) as ds:
            assert np.allclose(ds["lat"][:], lat4) and np.allclose(ds["lon"][:], lon4), "obs grid differs from the ELM 4 km grid"
            obs = {k: np.ma.filled(ds[f"soc_{k}cm"][:].astype("f8"), np.nan) for k, _, _ in DEPTHS}
        fig, axes = plt.subplots(2, 3, figsize=(21, 10.6), subplot_kw={"projection": ccrs.PlateCarree()})
        print(f"\n{short}, ELM mean of {len(years)} years {min(years)}-{max(years)}")
        for row, (k, label, rnd) in enumerate(DEPTHS):
            o4 = np.where(np.isfinite(elm4[k]), obs[k], np.nan)
            vmax = float(np.ceil(np.nanpercentile(np.concatenate([elm4[k].ravel(), o4.ravel(), elm05[k].ravel()]), 99.5) / rnd) * rnd)
            levels = np.linspace(0, vmax, 11)
            cmap = plt.get_cmap("YlOrBr", len(levels))
            cmap.set_bad("#dfe3e8")
            norm = BoundaryNorm(levels, ncolors=cmap.N, extend="max")
            s4 = stats(elm4[k], o4, w4)
            e4_05, wb = block_mean(elm4[k], w4)
            o_05, _ = block_mean(o4, w4)
            s05_agg, s05_nat = stats(e4_05, o_05, wb), stats(elm05[k], o_05, wb)
            s_nat_vs_agg = stats(elm05[k], e4_05, wb)
            print(f" {label}")
            print(f"  4 km cells, ELM 4 km vs obs: n={s4['n']} mean {s4['mean_a']:.2f} vs {s4['mean_b']:.2f}, {fmt(s4)}")
            print(f"  0.5°, ELM 4 km agg vs obs agg: mean {s05_agg['mean_a']:.2f} vs {s05_agg['mean_b']:.2f}, {fmt(s05_agg)}")
            print(f"  0.5°, ELM 0.5° native vs obs agg: mean {s05_nat['mean_a']:.2f} vs {s05_nat['mean_b']:.2f}, {fmt(s05_nat)}")
            print(f"  0.5°, ELM 0.5° native vs ELM 4 km agg: {fmt(s_nat_vs_agg)}")
            draw(axes[row, 0], lon4, lat4, elm4[k], cmap, norm, f"({'ab'[row]}1) ELM 4 km, SOC {label}")
            draw(axes[row, 1], lon4, lat4, o4, cmap, norm, f"({'ab'[row]}2) {obs_title}")
            mesh = draw(axes[row, 2], lon05, lat05, elm05[k], cmap, norm, f"({'ab'[row]}3) ELM 0.5°, SOC {label}")
            axes[row, 0].text(0.02, 0.03, f"vs obs (4 km cells): {fmt(s4)}", transform=axes[row, 0].transAxes,
                              fontsize=8.5, bbox=dict(fc="white", ec="none", alpha=0.75))
            axes[row, 2].text(0.02, 0.03, f"vs obs (0.5° cells): {fmt(s05_nat)}", transform=axes[row, 2].transAxes,
                              fontsize=8.5, bbox=dict(fc="white", ec="none", alpha=0.75))
            cb = fig.colorbar(mesh, ax=axes[row, :], orientation="horizontal", pad=0.07, shrink=0.45, aspect=45)
            cb.set_label(f"SOC {label}, kg C m$^{{-2}}$")
        fig.suptitle(f"Soil organic carbon: ELM vs {short}, ELM = mean of {min(years)}–{max(years)}",
                     x=0.04, y=0.995, ha="left", fontsize=13)
        fig.text(0.04, 0.005,
                 "ELM 0–30 cm: SOIL1–4C_vr integrated over the layers (partial layer by thickness); "
                 "0–100 cm: TOTSOMC_1m. Litter and CWD excluded. Observation masked where ELM 4 km has no soil column. "
                 "Grey = ocean/lakes. Statistics: area × landfrac weights; bias = ELM − obs.",
                 fontsize=8, color="#555555", va="bottom")
        out = os.path.join(OUT_DIR, f"soc_elm4km_{name}4km_elm0p5_{min(years)}-{max(years)}.png")
        fig.savefig(out, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved {out}")


if __name__ == "__main__":
    main()
