"""
One-row SOC 0-30 cm figure: ELM 4 km | ELM 0.5 deg | SoilGrids 2.0 | HWSD v1.2,
all on the ELM 4 km grid (the 0.5 deg run is copied to its 144 children,
comparator A of blueprint A4), mean of the annual ELM means 2000-2023, one
shared BrBG scale (0-12 kg C m-2, the poster's colormap).

A 4 km cell is shown and scored only where all four fields are valid (ELM 4 km,
copied 0.5 deg, SoilGrids, HWSD), so the two models and the two products are
compared on exactly the same cells. Statistics printed and annotated:
ELM 4 km and ELM 0.5 deg vs each product, and HWSD vs SoilGrids (the two
products' mutual agreement, a yardstick for how well any model can score).
HWSD v1.2 has a 0.05 deg source (coarser than 4 km): it is remapped, not
aggregated. First-look numbers, not the D6 evaluation.

Runs locally (cartopy venv), from the analysis root, after pulling the inputs
into _cache/ (see analysis_process_notes.md section 3.4):
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \
        code/figure1/plot_soc030_elm4km_elm0p5_soilgrids_hwsd.py
"""
import os
import sys

import cartopy.crs as ccrs
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
from matplotlib.colors import Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_agb_elm4km_esa4km_elm0p5 import BLOCK  # noqa: E402
from plot_elm_vs_esacci_agb import draw  # noqa: E402
from plot_soc_elm4km_obs4km_elm0p5 import ELM4_NPZ, ELM05_NPZ, OBS, OUT_DIR, fmt, stats  # noqa: E402

VMAX = 12.0  # kg C m-2, same as the 0-30 cm row of plot_soc_elm4km_obs4km_elm0p5.py


def main():
    e4, e05 = np.load(ELM4_NPZ), np.load(ELM05_NPZ)
    years = e4["year"].tolist()
    assert years == e05["year"].tolist() == list(range(2000, 2024)), "ELM extracts must both cover 2000-2023"
    lat4, lon4 = e4["lat"], e4["lon"]
    assert np.allclose(lat4.reshape(-1, BLOCK).mean(axis=1), e05["lat"]) and \
        np.allclose(lon4.reshape(-1, BLOCK).mean(axis=1), e05["lon"]), "0.5 deg grid is not the 12 x 12 block grid"
    w4 = e4["area"] * e4["landfrac"]
    elm4 = e4["soc_0_30_mean"].astype("f8")
    elm05c = np.kron(e05["soc_0_30_mean"].astype("f8"), np.ones((BLOCK, BLOCK)))
    obs = {}
    for name in ("soilgrids", "hwsd"):
        with netCDF4.Dataset(OBS[name][1]) as ds:
            assert np.allclose(ds["lat"][:], lat4) and np.allclose(ds["lon"][:], lon4), f"{name} grid differs from ELM 4 km"
            obs[name] = np.ma.filled(ds["soc_0_30cm"][:].astype("f8"), np.nan)

    common = np.isfinite(elm4) & np.isfinite(elm05c) & np.isfinite(obs["soilgrids"]) & np.isfinite(obs["hwsd"]) & (w4 > 0)
    m4, c05, sg, hw = (np.where(common, x, np.nan) for x in (elm4, elm05c, obs["soilgrids"], obs["hwsd"]))
    print(f"ELM mean of {len(years)} years {min(years)}-{max(years)}; SOC 0-30 cm; common support n={int(common.sum())} 4 km cells")
    S = {}
    for mname, m in [("ELM 4 km", m4), ("ELM 0.5° copied", c05)]:
        for oname, o in [("SoilGrids", sg), ("HWSD", hw)]:
            S[mname, oname] = stats(m, o, w4)
            s = S[mname, oname]
            print(f"  {mname:<16s} vs {oname:<9s}: mean {s['mean_a']:.2f} vs {s['mean_b']:.2f}, {fmt(s)}")
    S["HWSD", "SoilGrids"] = stats(hw, sg, w4)
    s = S["HWSD", "SoilGrids"]
    print(f"  {'HWSD':<16s} vs {'SoilGrids':<9s}: mean {s['mean_a']:.2f} vs {s['mean_b']:.2f}, {fmt(s)}")

    cmap = plt.get_cmap("BrBG").copy()
    cmap.set_bad("#dfe3e8")
    norm = Normalize(vmin=0.0, vmax=VMAX)
    fig, axes = plt.subplots(1, 4, figsize=(27, 5.6), subplot_kw={"projection": ccrs.PlateCarree()})
    draw(axes[0], lon4, lat4, m4, cmap, norm, "(a) ELM 4 km")
    draw(axes[1], lon4, lat4, c05, cmap, norm, "(b) ELM 0.5° (copied to 4 km)")
    draw(axes[2], lon4, lat4, sg, cmap, norm, "(c) SoilGrids 2.0")
    mesh = draw(axes[3], lon4, lat4, hw, cmap, norm, "(d) HWSD v1.2 (0.05° source)")

    def note(ax, lines):
        ax.text(0.02, 0.03, "\n".join(lines), transform=ax.transAxes, fontsize=8, va="bottom",
                bbox=dict(fc="white", ec="none", alpha=0.75))

    for ax, mname in ((axes[0], "ELM 4 km"), (axes[1], "ELM 0.5° copied")):
        note(ax, [f"vs SoilGrids: {fmt(S[mname, 'SoilGrids'])}", f"vs HWSD: {fmt(S[mname, 'HWSD'])}"])
    note(axes[3], [f"vs SoilGrids: {fmt(S['HWSD', 'SoilGrids'])}"])
    cb = fig.colorbar(mesh, ax=axes, orientation="horizontal", pad=0.08, shrink=0.35, aspect=45, extend="max")
    cb.set_label("SOC 0–30 cm, kg C m$^{-2}$")
    fig.suptitle(f"Soil organic carbon 0–30 cm: ELM (mean of {min(years)}–{max(years)}) vs SoilGrids and HWSD, all on the 4 km grid",
                 x=0.04, y=1.02, ha="left", fontsize=13)
    fig.text(0.04, 0.0,
             "ELM: SOIL1–4C_vr integrated over the layers (partial layer by thickness); litter and CWD excluded. "
             "The 0.5° run is copied to its 144 children; HWSD (0.05° source) is remapped, SoilGrids is requested on the 4 km grid.\n"
             "Only cells valid in all four fields are shown and scored. Grey = ocean/lakes/unscored. "
             "Statistics: area × landfrac weights; bias = first − second; HWSD vs SoilGrids shows how well the two products agree.",
             fontsize=8, color="#555555", va="top")
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"soc030_elm4km_elm0p5_soilgrids_hwsd_{min(years)}-{max(years)}.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
