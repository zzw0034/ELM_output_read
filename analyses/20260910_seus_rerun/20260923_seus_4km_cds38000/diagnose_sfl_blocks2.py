"""
Second pass on the south-Florida GPP patches (see diagnose_sfl_blocks.py).

The first pass correlated |neighbour differences| over all ~7000 edges, which
is dominated by many small edges. Here each candidate is tested on ITS OWN
sharp edges instead:

  jump_ratio  = mean |dGPP| across the candidate's sharp edges
                / mean |dGPP| across all other edges
                (candidate's sharp edges = its top 5 % |d|, or all its non-zero
                edges if fewer than 5 % are non-zero, i.e. piecewise-constant
                fields). >> 1: GPP jumps where the candidate jumps.
  signed_corr = correlation of signed dGPP with signed dCandidate over the
                candidate's sharp edges (same-direction jumps).
  n_sharp     = number of those edges.

Also reports, for the forcing fields, how blocky they are: fraction of edges
with exactly zero difference, and for non-zero edges the distribution of the
global edge index modulo 3 (edges at -95 + k/24 and 24 + k/24).

Plus zoomed panels (no overlays) of GPP and the main candidates over two
sub-boxes: NW mosaic (27.0-28.6N, 82.8-81.2W) and SE of Lake Okeechobee
(25.3-27.2N, 81.6-80.0W).

Run through Slurm:  sbatch -J sfl_blocks2 submit_py.sbatch diagnose_sfl_blocks2.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import OUTDIR, PERIODS, LATE, JAN, _read, case_name, h0_climatology, load_grid
from diagnose_sfl_blocks import (BOX_LAT, BOX_LON, LANDUSE, FSURDAT, H0_VARS, SURF_2D, SURF_3D,
                                 SSP, check_coords)

ZOOMS = {"NW mosaic": ((27.0, 28.6), (-82.8, -81.2)),
         "SE of Lake Okeechobee": ((25.3, 27.2), (-81.6, -80.0))}
ZOOM_FIELDS = ["GPP oldDF (annual)", "GPP Default (annual)", "TLAI oldDF", "FPG oldDF", "FPG_P oldDF",
               "LU PCT_NATVEG", "LU2100 grass %", "LU2100 C4 share of grass", "surf FMAX",
               "surf SOIL_ORDER", "surf LABILE_P", "NDEP_TO_SMINN oldDF", "RAIN oldDF", "TBOT oldDF",
               "FSDS oldDF"]


def edges(fld):
    """signed neighbour differences and their global edge indices, x then y."""
    dx = np.diff(fld, axis=1); dy = np.diff(fld, axis=0)
    kx = np.broadcast_to(np.arange(1, fld.shape[1]) + COL0, dx.shape)
    ky = np.broadcast_to((np.arange(1, fld.shape[0]) + ROW0)[:, None], dy.shape)
    return dx, dy, kx, ky


def flat(dx, dy, okx, oky):
    return np.concatenate([dx[okx], dy[oky]])


def main():
    global COL0, ROW0
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    jj = np.where((lat >= BOX_LAT[0]) & (lat <= BOX_LAT[1]))[0]
    ii = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    ROW0, COL0 = jj[0], ii[0]
    sub = (slice(jj[0], jj[-1] + 1), slice(ii[0], ii[-1] + 1))
    land = (W > 0)[sub]
    slat, slon = lat[jj], lon[ii]

    F = {}
    old = case_name("oldDF", SSP)
    ann, mon = h0_climatology(old, "GPP", PERIODS[LATE])
    F["GPP oldDF (annual)"] = ann[sub]; F["GPP oldDF (Jan)"] = mon[JAN][sub]
    for v in H0_VARS:
        F[f"{v} oldDF"] = h0_climatology(old, v, PERIODS[LATE])[0][sub]
    F["GPP Default (annual)"] = h0_climatology(case_name("Default", SSP), "GPP", PERIODS[LATE])[0][sub]
    with Dataset(LANDUSE) as ds:
        check_coords(ds, lat, lon, LANDUSE)
        t = int(np.where(np.asarray(ds.variables["YEAR"][:]).astype(int) == 2100)[0][0])
        p = _read(ds, "PCT_NAT_PFT")[t]
        grass = p[12:15].sum(0)
        with np.errstate(invalid="ignore", divide="ignore"):
            F["LU2100 C4 share of grass"] = np.where(grass > 0, p[14] / grass, np.nan)[sub]
        F["LU2100 grass %"] = grass[sub]
        F["LU2100 crop PFT15 %"] = p[15][sub]
        F["LU2100 bare %"] = p[0][sub]
        F["LU2100 shrub 9-11 %"] = p[9:12].sum(0)[sub]
        F["LU PCT_NATVEG"] = _read(ds, "PCT_NATVEG")[sub]
    with Dataset(FSURDAT) as ds:
        check_coords(ds, lat, lon, FSURDAT)
        for v in SURF_2D:
            F[f"surf {v}"] = _read(ds, v)[sub]
        for v in SURF_3D:
            F[f"surf {v} (top)"] = _read(ds, v)[0][sub]
        for v in ("PCT_WETLAND", "PCT_LAKE", "PCT_URBAN", "PCT_GLACIER"):
            if v in ds.variables:
                x = _read(ds, v)
                F[f"surf {v}"] = (x.sum(0) if x.ndim == 3 else x)[sub]
    for k in F:
        F[k] = np.where(land, F[k], np.nan)

    gx, gy, kx, ky = edges(F["GPP oldDF (annual)"])
    lines = [f"South Florida {BOX_LAT}N {BOX_LON}E, {land.sum()} land cells, {LATE} mean for model fields",
             "jump_ratio = mean|dGPP| on the candidate's sharp edges / on all other edges (>>1: GPP jumps there)",
             "signed_corr = corr(dGPP, dCandidate) on the candidate's sharp edges", "",
             f"{'candidate':32s}{'n_sharp':>9s}{'jump_ratio':>12s}{'signed_corr':>13s}"]
    results = []
    for name, fld in F.items():
        if name.startswith("GPP oldDF (annual)"):
            continue
        cx, cy, _, _ = edges(fld)
        okx = np.isfinite(gx) & np.isfinite(cx); oky = np.isfinite(gy) & np.isfinite(cy)
        g = flat(gx, gy, okx, oky); c = flat(cx, cy, okx, oky)
        ac = np.abs(c)
        nz = ac > 1e-12 * max(np.nanmax(ac), 1e-30)
        sharp = nz if nz.mean() < 0.05 else ac >= np.percentile(ac, 95)
        if sharp.sum() < 5 or (~sharp).sum() < 5:
            lines.append(f"{name:32s}{int(sharp.sum()):9d}{'--':>12s}{'--':>13s}")
            continue
        jr = np.abs(g[sharp]).mean() / np.abs(g[~sharp]).mean()
        sc = np.corrcoef(g[sharp], c[sharp])[0, 1] if c[sharp].std() > 0 else np.nan
        results.append((jr, name))
        lines.append(f"{name:32s}{int(sharp.sum()):9d}{jr:12.2f}{sc:13.2f}")

    lines += ["", "Forcing blockiness: fraction of edges with zero difference; non-zero edges by k mod 3"]
    for v in ("TBOT", "RAIN", "FSDS", "FLDS", "QBOT", "WIND"):
        dx, dy, ex, ey = edges(F[f"{v} oldDF"])
        okx = np.isfinite(dx); oky = np.isfinite(dy)
        d = flat(dx, dy, okx, oky); k = flat(ex, ey, okx, oky)
        zero = np.abs(d) < 1e-9 * np.nanmax(np.abs(d))
        m = np.bincount(k[~zero] % 3, minlength=3) / max((~zero).sum(), 1)
        lines.append(f"  {v:6s} zero-diff edges {zero.mean():6.1%}   non-zero k%3 = 0/1/2: "
                     f"{m[0]:.2f} / {m[1]:.2f} / {m[2]:.2f}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUTDIR, "sfl_blocks2_summary.txt"), "w") as f:
        f.write(txt + "\n")

    # zoomed panels, no overlays
    for zname, (zlat, zlon) in ZOOMS.items():
        zj = (slat >= zlat[0]) & (slat <= zlat[1]); zi = (slon >= zlon[0]) & (slon <= zlon[1])
        ncol = 5; nrow = int(np.ceil(len(ZOOM_FIELDS) / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 4.4 * nrow))
        for ax, name in zip(axes.flat, ZOOM_FIELDS):
            fld = F[name][np.ix_(zj, zi)]
            lo, hi = np.nanpercentile(fld, [1, 99])
            if hi <= lo:
                hi = lo + 1e-12
            pc = ax.pcolormesh(slon[zi], slat[zj], fld, cmap="viridis", vmin=lo, vmax=hi, shading="nearest")
            ax.set_aspect("equal"); ax.set_title(name, fontsize=9); ax.tick_params(labelsize=7)
            fig.colorbar(pc, ax=ax, shrink=0.7).ax.tick_params(labelsize=7)
        for ax in list(axes.flat)[len(ZOOM_FIELDS):]:
            ax.axis("off")
        fig.suptitle(f"{zname}: {zlat[0]}-{zlat[1]}N, {zlon[0]}-{zlon[1]}E (no overlays)", fontsize=13)
        fig.tight_layout()
        out = os.path.join(OUTDIR, f"sfl_blocks2_zoom_{zname.split()[0]}.png")
        fig.savefig(out, dpi=130)
        plt.close(fig)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
