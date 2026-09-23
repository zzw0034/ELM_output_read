"""
Which PFTs make the bright single cells in JANUARY GPP of the 38000 s DF run
(south Florida, e.g. 27.3-28.6 N)?

At 38000 s all stress-deciduous PFTs (6, 10, 13, 14, 15, 16) are dormant in
January, so a cell can only be green then if it holds PFTs the threshold does
not govern (e.g. evergreen shrub BES_temp = 9; DF removes trees but keeps
shrubs). diagnose_sfl_jan.py ruled out winter rain, temperature, soil water.

From h1 (newDF, January of 2091-2100): each PFT's contribution to grid-cell
January GPP = GPP_p * pfts1d_wtgcell (the same weighting that makes the h0
grid-cell value, checked earlier: h1 sum / h0 total = 1.0000). Reports the
mean contribution by PFT for the brightest 2 % of land cells in the box
versus all other cells, and maps each PFT group's contribution (no overlays).

Run through Slurm:  sbatch -J sfl_janpft submit_py.sbatch diagnose_sfl_jan_pft.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import (OUTDIR, PERIODS, LATE, JAN, PFT_NAMES, STRESS_DECID, SEC_PER_YEAR,
                                  VEG_LUNITS, _read, _check_year, case_name, hist_file, load_grid)
from diagnose_sfl_blocks import BOX_LAT, BOX_LON, SSP

GROUPS = {
    "stress-deciduous (6,10,13-16)": sorted(STRESS_DECID),
    "evergreen shrub BES_temp (9)": [9],
    "boreal shrub BDS_boreal (11)": [11],
    "arctic C3 grass (12)": [12],
    "trees (1-8, excl. 6)": [1, 2, 3, 4, 5, 7, 8],
}


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    jj = np.where((lat >= BOX_LAT[0]) & (lat <= BOX_LAT[1]))[0]
    ii = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    nlat, nlon = len(lat), len(lon)
    case = case_name("newDF", SSP)
    contrib = {t: np.zeros((nlat, nlon)) for t in PFT_NAMES}   # gC/m2/yr, grid-cell basis
    frac = {t: np.zeros((nlat, nlon)) for t in PFT_NAMES}
    years = PERIODS[LATE]
    for y in years:
        path = hist_file(case, "h1", y)
        print(f"  {os.path.basename(path)}", flush=True)
        with Dataset(path) as ds:
            _check_year(ds, y, path)
            itype = np.asarray(ds.variables["pfts1d_itype_veg"][:]).astype(int)
            lunit = np.asarray(ds.variables["pfts1d_itype_lunit"][:]).astype(int)
            ixy = np.asarray(ds.variables["pfts1d_ixy"][:]).astype(int) - 1
            jxy = np.asarray(ds.variables["pfts1d_jxy"][:]).astype(int) - 1
            wtg = np.nan_to_num(_read(ds, "pfts1d_wtgcell"))
            g = ds.variables["GPP"][JAN, :]
            g = np.ma.filled(g.astype(float), np.nan) * SEC_PER_YEAR
        veg = np.isin(lunit, VEG_LUNITS) & (wtg > 0)
        for t in PFT_NAMES:
            s = veg & (itype == t)
            np.add.at(contrib[t], (jxy[s], ixy[s]), np.nan_to_num(g[s]) * wtg[s] / len(years))
            np.add.at(frac[t], (jxy[s], ixy[s]), wtg[s] * 100 / len(years))
    sub = (slice(jj[0], jj[-1] + 1), slice(ii[0], ii[-1] + 1))
    land = (W > 0)[sub]
    total = sum(contrib[t] for t in PFT_NAMES)[sub]
    total = np.where(land, total, np.nan)
    thr = np.nanpercentile(total, 98)
    bright = land & (total >= thr)
    rest = land & ~bright
    lines = [f"newDF ({case}) January GPP, {LATE} mean, south Florida {BOX_LAT}N {BOX_LON}E",
             f"bright = top 2 % of land cells (Jan GPP >= {thr:.0f} gC/m2/yr annualised): {bright.sum()} cells; "
             f"other cells: {rest.sum()}",
             f"mean grid-cell Jan GPP: bright {np.nanmean(total[bright]):.0f}, other {np.nanmean(total[rest]):.0f}",
             "", f"{'PFT':>22s}{'area% bright':>14s}{'area% other':>13s}{'GPP bright':>12s}{'GPP other':>11s}"]
    for t in PFT_NAMES:
        c = contrib[t][sub]; f = frac[t][sub]
        if np.nanmax(f[land]) < 0.01:
            continue
        star = "*" if t in STRESS_DECID else " "
        lines.append(f"{star}{t:2d} {PFT_NAMES[t]:>18s}{f[bright].mean():14.1f}{f[rest].mean():13.1f}"
                     f"{c[bright].mean():12.1f}{c[rest].mean():11.1f}")
    lines.append("(* = stress-deciduous; GPP columns = contribution to grid-cell Jan GPP, gC/m2/yr annualised)")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUTDIR, "sfl_jan_pft_summary.txt"), "w") as fh:
        fh.write(txt + "\n")

    slat, slon = lat[jj], lon[ii]
    panels = [("Jan GPP newDF, total", total)]
    for gname, ts in GROUPS.items():
        panels.append((f"Jan GPP from {gname}", np.where(land, sum(contrib[t] for t in ts)[sub], np.nan)))
    panels.append(("area % evergreen shrub BES_temp (9)", np.where(land, frac[9][sub], np.nan)))
    fig, axes = plt.subplots(2, 4, figsize=(20, 11))
    vmax = np.nanpercentile(total, 99.5)
    for ax, (name, fld) in zip(axes.flat, panels):
        hi = vmax if name.startswith("Jan GPP") else np.nanpercentile(fld, 99.5)
        pc = ax.pcolormesh(slon, slat, fld, cmap="viridis", vmin=0, vmax=max(hi, 1e-9), shading="nearest")
        ax.set_aspect("equal"); ax.set_title(name, fontsize=10); ax.tick_params(labelsize=7)
        fig.colorbar(pc, ax=ax, shrink=0.7).ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(panels):]:
        ax.axis("off")
    fig.suptitle(f"South Florida, newDF ssp585, January GPP by PFT group, {LATE} (no overlays)", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "sfl_jan_pft_panels.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
