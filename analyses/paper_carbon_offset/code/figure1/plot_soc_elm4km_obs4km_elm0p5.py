"""
Soil organic carbon maps, one figure per observation product:
rows = depth (0-30 cm, 0-100 cm); columns = ELM 4 km | observation on the
ELM 4 km grid | ELM 0.5 deg copied to the 4 km grid. ELM is the mean of the
annual means 2000-2023.

EVERYTHING IS ON THE 4 KM GRID. The 0.5 deg run is disaggregated by copying
each 0.5 deg cell to its 12 x 12 children (comparator "A" of blueprint A4);
SOC has no land-cover downscaling (B) because all natural PFTs share one soil
column (blueprint D6 step 5). The copy therefore carries no within-cell
information; its skill at 4 km shows what a coarse run knows. Because 0.5 deg
and 4 km land masks differ at the coast, a child cell is shown/scored only if
ELM 4 km, the observation and the copied 0.5 deg value are ALL valid (the
observation is also masked where ELM 4 km has no soil column), so both models
are scored on exactly the same cells.

Observation: HWSD v1.2 (0.05 deg source, so remapped, not aggregated) or
SoilGrids 2.0 (WCS request on the ELM grid); see analysis_process_notes.md
section 3.4.

Statistics printed per row (area x landfrac weights, common support;
first-look numbers, not the D6 evaluation): ELM 4 km vs obs, ELM 0.5 deg
(copied) vs obs, ELM 0.5 deg (copied) vs ELM 4 km.

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
from plot_agb_elm4km_esa4km_elm0p5 import BLOCK  # noqa: E402
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
# key, label, colour-scale top (kg C m-2). Fixed and shared by both products so the
# figures are comparable and wetland/peat hotspots (Everglades, Mississippi
# delta, NC pocosins; up to ~50-65 kg C m-2 in 0-100 cm) saturate instead of
# stretching the scale and washing out ELM. 12 equal bins, extend="max".
DEPTHS = [("0_30", "0–30 cm", 12.0), ("0_100", "0–100 cm", 36.0)]


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
    # disaggregate 0.5 deg -> 4 km by copying each cell to its BLOCK x BLOCK children
    elm05c = {k: np.kron(e05[f"soc_{k}_mean"].astype("f8"), np.ones((BLOCK, BLOCK))) for k, _, _ in DEPTHS}
    os.makedirs(OUT_DIR, exist_ok=True)

    for name in which:
        short, path, obs_title = OBS[name]
        with netCDF4.Dataset(path) as ds:
            assert np.allclose(ds["lat"][:], lat4) and np.allclose(ds["lon"][:], lon4), "obs grid differs from the ELM 4 km grid"
            obs = {k: np.ma.filled(ds[f"soc_{k}cm"][:].astype("f8"), np.nan) for k, _, _ in DEPTHS}
        fig, axes = plt.subplots(2, 3, figsize=(21, 10.6), subplot_kw={"projection": ccrs.PlateCarree()})
        print(f"\n{short}, ELM mean of {len(years)} years {min(years)}-{max(years)}; all on the 4 km grid")
        for row, (k, label, vmax) in enumerate(DEPTHS):
            common = np.isfinite(elm4[k]) & np.isfinite(obs[k]) & np.isfinite(elm05c[k])
            lost = int((np.isfinite(elm4[k]) & np.isfinite(obs[k]) & ~np.isfinite(elm05c[k])).sum())
            m4, o4, c05 = (np.where(common, x[k], np.nan) for x in (elm4, obs, elm05c))
            levels = np.linspace(0, vmax, 13)
            cmap = plt.get_cmap("YlOrBr", len(levels))
            cmap.set_bad("#dfe3e8")
            norm = BoundaryNorm(levels, ncolors=cmap.N, extend="max")
            s4, s05, s_mm = stats(m4, o4, w4), stats(c05, o4, w4), stats(c05, m4, w4)
            print(f" {label}: common support n={s4['n']} 4 km cells "
                  f"({lost} cells valid in ELM 4 km and obs but without a 0.5 deg parent value are dropped)")
            print(f"  ELM 4 km vs obs:           mean {s4['mean_a']:.2f} vs {s4['mean_b']:.2f}, {fmt(s4)}")
            print(f"  ELM 0.5° copied vs obs:    mean {s05['mean_a']:.2f} vs {s05['mean_b']:.2f}, {fmt(s05)}")
            print(f"  ELM 0.5° copied vs ELM 4 km: {fmt(s_mm)}")
            draw(axes[row, 0], lon4, lat4, m4, cmap, norm, f"({'ab'[row]}1) ELM 4 km, SOC {label}")
            draw(axes[row, 1], lon4, lat4, o4, cmap, norm, f"({'ab'[row]}2) {obs_title}")
            mesh = draw(axes[row, 2], lon4, lat4, c05, cmap, norm, f"({'ab'[row]}3) ELM 0.5° copied to 4 km, SOC {label}")
            axes[row, 0].text(0.02, 0.03, f"vs obs: {fmt(s4)}", transform=axes[row, 0].transAxes,
                              fontsize=8.5, bbox=dict(fc="white", ec="none", alpha=0.75))
            axes[row, 2].text(0.02, 0.03, f"vs obs: {fmt(s05)}", transform=axes[row, 2].transAxes,
                              fontsize=8.5, bbox=dict(fc="white", ec="none", alpha=0.75))
            cb = fig.colorbar(mesh, ax=axes[row, :], orientation="horizontal", pad=0.07, shrink=0.45, aspect=45)
            cb.set_label(f"SOC {label}, kg C m$^{{-2}}$")
        fig.suptitle(f"Soil organic carbon: ELM vs {short}, ELM = mean of {min(years)}–{max(years)}",
                     x=0.04, y=0.995, ha="left", fontsize=13)
        fig.text(0.04, 0.005,
                 "ELM 0–30 cm: SOIL1–4C_vr integrated over the layers (partial layer by thickness); 0–100 cm: TOTSOMC_1m. "
                 "Litter and CWD excluded.\n"
                 "All panels on the 4 km grid: the 0.5° run is copied to its 144 children, the observation is masked where ELM 4 km "
                 "has no soil column, and only cells valid in all three fields are shown and scored.\n"
                 "Grey = ocean/lakes/unscored. Statistics: area × landfrac weights; bias = ELM − obs.",
                 fontsize=8, color="#555555", va="bottom")
        out = os.path.join(OUT_DIR, f"soc_elm4km_{name}4km_elm0p5_{min(years)}-{max(years)}.png")
        fig.savefig(out, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved {out}")


if __name__ == "__main__":
    main()
