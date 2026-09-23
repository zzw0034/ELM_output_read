"""
Third pass on the south-Florida GPP pattern: the long, nearly straight
north-south boundary near 81 W, 25.4-26.9 N, south-east of Lake Okeechobee.
East of it GPP / LAI are high and N limitation is weak (FPG high); west of it
the opposite. It is present in the old Default run too, so it is neither the
DF land use nor crit_dayl_stress. Passes 1-2 (diagnose_sfl_blocks*.py) found
no match among the forcing, soil P/texture/organic, soil order/colour, FMAX,
N/P deposition, or DF grass/C4 fractions.

Method:
 1. For every row in 25.4-26.9 N, find the west->east edge with the largest
    TLAI increase between 81.5 W and 80.6 W. Report where these edges sit
    (global edge index k: lon edge = -95 + k/24).
 2. For each candidate field, compare its |difference| across exactly those
    edges with the median |difference| across all other east-west edges in
    the same sub-box (edge_ratio), and report the median signed difference
    (east minus west) across the boundary.
 3. Zoomed panels (no overlays) of TLAI and the 11 best-matching candidates.

Candidates: every 2-D numeric field of the surface dataset (plus top layer of
PCT_SAND / PCT_CLAY / ORGANIC), DF land use in 2024 and 2100, the old
Default land use in 2024, and model output (2091-2100 mean) incl. fire and
hydrology diagnostics.

Run through Slurm:  sbatch -J sfl_edge submit_py.sbatch diagnose_sfl_edge81w.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import OUTDIR, PERIODS, LATE, _read, case_name, h0_climatology, load_grid
from diagnose_sfl_blocks import LANDUSE, FSURDAT, SSP, check_coords

BOX_LAT = (25.3, 27.2)
BOX_LON = (-81.8, -80.0)
ROW_LAT = (25.4, 26.9)
EDGE_LON = (-81.5, -80.6)
LANDUSE_DEFAULT = ("/projects/hpcl-cli185/proj-shared/zw5/ELM_Futu_landuseInput/outputs/processed/"
                   "landuse.timeseries_SEUS_1_24deg_nlcd2elm_SSP5_RCP85_simyr2024-2100.nc")
H0 = ["TLAI", "GPP", "FPG", "FPG_P", "BTRAN", "FAREA_BURNED", "NFIRE", "FIRE", "ZWT", "QOVER",
      "QDRAI", "H2OSOI", "TSOI", "SMINN", "SMIN_NO3", "SMIN_NH4", "TOTSOMC", "TOTLITC", "TOTVEGC",
      "HR", "NEE", "TBOT", "RAIN", "FSDS", "QBOT", "WIND", "NDEP_TO_SMINN"]
SKIP_SURF = {"LONGXY", "LATIXY", "AREA", "PFTDATA_MASK", "LANDFRAC_PFT"}


def lu_fields(path, year, tag, sub, lat, lon):
    out = {}
    with Dataset(path) as ds:
        check_coords(ds, lat, lon, path)
        t = int(np.where(np.asarray(ds.variables["YEAR"][:]).astype(int) == year)[0][0])
        p = _read(ds, "PCT_NAT_PFT")[t]
        out[f"{tag}{year} tree %"] = p[1:9].sum(0)[sub]
        out[f"{tag}{year} evergreen NET_temp %"] = p[1][sub]
        out[f"{tag}{year} BDT_temp %"] = p[7][sub]
        out[f"{tag}{year} shrub %"] = p[9:12].sum(0)[sub]
        out[f"{tag}{year} C3 grass %"] = p[13][sub]
        out[f"{tag}{year} C4 grass %"] = p[14][sub]
        out[f"{tag}{year} crop15 %"] = p[15][sub]
        out[f"{tag}{year} bare %"] = p[0][sub]
        for v in [x for x in ds.variables if x.startswith("HARVEST")]:
            h = _read(ds, v)
            out[f"{tag}{year} {v}"] = (h[t] if h.ndim == 3 else h)[sub]
    return out


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    jj = np.where((lat >= BOX_LAT[0]) & (lat <= BOX_LAT[1]))[0]
    ii = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    sub = (slice(jj[0], jj[-1] + 1), slice(ii[0], ii[-1] + 1))
    land = (W > 0)[sub]
    slat, slon = lat[jj], lon[ii]

    F = {}
    old = case_name("oldDF", SSP)
    for v in H0:
        a, _ = h0_climatology(old, v, PERIODS[LATE])
        F[f"{v} oldDF"] = (a[0] if a.ndim == 3 else a)[sub]
    F["TLAI Default"] = h0_climatology(case_name("Default", SSP), "TLAI", PERIODS[LATE])[0][sub]
    F.update(lu_fields(LANDUSE, 2024, "DF", sub, lat, lon))
    F.update(lu_fields(LANDUSE, 2100, "DF", sub, lat, lon))
    F.update(lu_fields(LANDUSE_DEFAULT, 2024, "Def", sub, lat, lon))
    with Dataset(FSURDAT) as ds:
        check_coords(ds, lat, lon, FSURDAT)
        for v, var in ds.variables.items():
            if v in SKIP_SURF or var.dimensions[-2:] != ("lsmlat", "lsmlon"):
                continue
            x = _read(ds, v)
            if x.ndim == 2:
                F[f"surf {v}"] = x[sub]
            elif x.ndim == 3 and v in ("PCT_SAND", "PCT_CLAY", "ORGANIC", "PCT_URBAN"):
                F[f"surf {v}"] = (x.sum(0) if v == "PCT_URBAN" else x[0])[sub]
    for k in F:
        F[k] = np.where(land, F[k].astype(float), np.nan)

    # 1. locate the boundary from TLAI
    tl = F["TLAI oldDF"]
    dx = np.diff(tl, axis=1)                       # east minus west, edge between i and i+1
    rows = np.where((slat >= ROW_LAT[0]) & (slat <= ROW_LAT[1]))[0]
    cols = np.where((slon[:-1] >= EDGE_LON[0]) & (slon[1:] <= EDGE_LON[1]))[0]
    picks = []
    for r in rows:
        d = dx[r, cols]
        if np.all(~np.isfinite(d)):
            continue
        c = cols[int(np.nanargmax(d))]
        picks.append((r, c, dx[r, c]))
    k_of = lambda c: ii[0] + c + 1                 # global edge index of edge right of local col c
    ks = np.array([k_of(c) for _, c, _ in picks])
    lines = [f"Boundary search: rows {ROW_LAT[0]}-{ROW_LAT[1]}N, edges {EDGE_LON[0]}..{EDGE_LON[1]}E",
             f"{len(picks)} rows; TLAI jump at the picked edge: median {np.median([p[2] for p in picks]):.2f}"
             f" (typical |dTLAI| elsewhere {np.nanmedian(np.abs(dx)):.2f})",
             "edge longitude (lon = -95 + k/24) -> number of rows:"]
    uk, cnt = np.unique(ks, return_counts=True)
    for k, n in zip(uk, cnt):
        lines.append(f"   k={k:4d}  lon={-95 + k / 24:9.4f}  k%3={k % 3} k%6={k % 6} k%12={k % 12}  rows={n}")

    # 2. which candidate jumps across exactly those edges?
    sel = np.zeros(dx.shape, bool)
    for r, c, _ in picks:
        sel[r, c] = True
    box = np.zeros(dx.shape, bool)
    box[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1] = True
    res = []
    for name, fld in F.items():
        d = np.diff(fld, axis=1)
        on = d[sel & np.isfinite(d)]
        off = np.abs(d[box & ~sel & np.isfinite(d)])
        if on.size < 5 or off.size < 5:
            continue
        base = np.median(off)
        scale = base if base > 0 else (np.mean(off) if np.mean(off) > 0 else np.nan)
        ratio = np.median(np.abs(on)) / scale if scale == scale and scale > 0 else (np.inf if np.any(on != 0) else 0.0)
        frac_nz = np.mean(np.abs(on) > 0)
        res.append((ratio, name, np.median(on), frac_nz))
    res.sort(key=lambda x: -np.nan_to_num(x[0], nan=-1, posinf=1e9))
    lines += ["", "edge_ratio = median |d| across the boundary edges / median |d| across other E-W edges in the box",
              "signed = median (east - west) across the boundary; nonzero = share of boundary edges where the field changes",
              f"{'candidate':34s}{'edge_ratio':>12s}{'signed':>12s}{'nonzero':>9s}"]
    for ratio, name, med, fnz in res:
        lines.append(f"{name:34s}{ratio:12.2f}{med:12.4g}{fnz:9.2f}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUTDIR, "sfl_edge81w_summary.txt"), "w") as f:
        f.write(txt + "\n")

    # 3. panels
    top = ["TLAI oldDF", "TLAI Default"] + [n for _, n, _, _ in res if n not in ("TLAI oldDF", "TLAI Default")][:13]
    ncol = 5
    nrow = int(np.ceil(len(top) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 4.8 * nrow))
    for ax, name in zip(axes.flat, top):
        fld = F[name]
        lo, hi = np.nanpercentile(fld, [1, 99])
        if hi <= lo:
            hi = lo + 1e-12
        pc = ax.pcolormesh(slon, slat, fld, cmap="viridis", vmin=lo, vmax=hi, shading="nearest")
        ax.set_aspect("equal"); ax.set_title(name, fontsize=9); ax.tick_params(labelsize=7)
        fig.colorbar(pc, ax=ax, shrink=0.7).ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(top):]:
        ax.axis("off")
    fig.suptitle(f"SE of Lake Okeechobee {BOX_LAT}N {BOX_LON}E: TLAI and best-matching candidates "
                 "for the ~81W boundary (no overlays)", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "sfl_edge81w_panels.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
