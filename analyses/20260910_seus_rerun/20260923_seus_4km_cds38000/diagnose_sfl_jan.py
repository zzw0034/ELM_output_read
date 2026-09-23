"""
Why does JANUARY GPP of the 38000 s DF run show square patches in south
Florida when annual GPP barely does?

Hypothesis: at 38000 s every cell is force-dormant from Nov/Dec until late
January (25.25N: until ~Jan 12; 29N: ~Jan 27). After daylength recovers,
onset still needs 15 wet-soil days (onset_swi) and >= 20 mm of rain in the
last 10 days (cumprec_onset), so January GPP is set by WHEN each cell greens
up -- i.e. by the winter (dry-season) rainfall pattern of the forcing, which
matters little for the annual total.

Test on the south-Florida box: jump_ratio / signed_corr (same metric as
diagnose_sfl_blocks2.py) of January GPP of newDF against January TLAI, the
Nov/Dec/Jan climatological RAIN, TBOT, FSDS, top-layer H2OSOI, BTRAN, and the
static PCT_NATVEG; plus the same for oldDF January GPP for contrast.
Zoomed panels, no overlays.

Run through Slurm:  sbatch -J sfl_jan submit_py.sbatch diagnose_sfl_jan.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import OUTDIR, PERIODS, LATE, JAN, _read, case_name, h0_climatology, load_grid
from diagnose_sfl_blocks import BOX_LAT, BOX_LON, LANDUSE, SSP, check_coords

NOV, DEC = 10, 11
ZOOM = ((25.3, 28.6), (-82.8, -80.0))


def jump(ref, cand):
    rx, ry = np.diff(ref, axis=1), np.diff(ref, axis=0)
    cx, cy = np.diff(cand, axis=1), np.diff(cand, axis=0)
    okx = np.isfinite(rx) & np.isfinite(cx); oky = np.isfinite(ry) & np.isfinite(cy)
    g = np.concatenate([rx[okx], ry[oky]]); c = np.concatenate([cx[okx], cy[oky]])
    ac = np.abs(c)
    nz = ac > 1e-12 * max(ac.max(), 1e-30)
    sharp = nz if nz.mean() < 0.05 else ac >= np.percentile(ac, 95)
    jr = np.abs(g[sharp]).mean() / np.abs(g[~sharp]).mean()
    sc = np.corrcoef(g[sharp], c[sharp])[0, 1] if c[sharp].std() > 0 else np.nan
    return jr, sc


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    jj = np.where((lat >= BOX_LAT[0]) & (lat <= BOX_LAT[1]))[0]
    ii = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    sub = (slice(jj[0], jj[-1] + 1), slice(ii[0], ii[-1] + 1))
    land = (W > 0)[sub]
    slat, slon = lat[jj], lon[ii]

    F = {}
    for run in ("newDF", "oldDF"):
        c = case_name(run, SSP)
        _, mon = h0_climatology(c, "GPP", PERIODS[LATE])
        F[f"Jan GPP {run}"] = mon[JAN][sub]
        _, mon = h0_climatology(c, "TLAI", PERIODS[LATE])
        F[f"Jan TLAI {run}"] = mon[JAN][sub]
    c = case_name("newDF", SSP)
    _, rain = h0_climatology(c, "RAIN", PERIODS[LATE])
    for m, lab in ((NOV, "Nov"), (DEC, "Dec"), (JAN, "Jan")):
        F[f"{lab} RAIN"] = rain[m][sub]
    F["Nov+Dec+Jan RAIN"] = (rain[NOV] + rain[DEC] + rain[JAN])[sub]
    for v in ("TBOT", "FSDS", "BTRAN"):
        _, mon = h0_climatology(c, v, PERIODS[LATE])
        F[f"Jan {v}"] = mon[JAN][sub]
    _, mon = h0_climatology(c, "H2OSOI", PERIODS[LATE])
    F["Jan H2OSOI top"] = mon[JAN][0][sub]
    F["Dec H2OSOI top"] = mon[DEC][0][sub]
    with Dataset(LANDUSE) as ds:
        check_coords(ds, lat, lon, LANDUSE)
        F["PCT_NATVEG"] = _read(ds, "PCT_NATVEG")[sub]
    for k in F:
        F[k] = np.where(land, F[k], np.nan)

    lines = [f"South Florida {BOX_LAT}N {BOX_LON}E, {LATE} monthly climatology",
             "jump_ratio / signed_corr of the reference field's edges on each candidate's sharp edges",
             f"{'candidate':22s}{'ref: Jan GPP newDF':>24s}{'ref: Jan GPP oldDF':>24s}"]
    for name in F:
        if name.startswith("Jan GPP"):
            continue
        a = jump(F["Jan GPP newDF"], F[name]); b = jump(F["Jan GPP oldDF"], F[name])
        lines.append(f"{name:22s}{a[0]:12.2f}{a[1]:12.2f}{b[0]:12.2f}{b[1]:12.2f}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUTDIR, "sfl_jan_summary.txt"), "w") as f:
        f.write(txt + "\n")

    zj = (slat >= ZOOM[0][0]) & (slat <= ZOOM[0][1]); zi = (slon >= ZOOM[1][0]) & (slon <= ZOOM[1][1])
    names = list(F)
    ncol = 5; nrow = int(np.ceil(len(names) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.4 * ncol, 5.2 * nrow))
    for ax, name in zip(axes.flat, names):
        fld = F[name][np.ix_(zj, zi)]
        lo, hi = np.nanpercentile(fld, [1, 99])
        if hi <= lo:
            hi = lo + 1e-12
        pc = ax.pcolormesh(slon[zi], slat[zj], fld, cmap="viridis", vmin=lo, vmax=hi, shading="nearest")
        ax.set_aspect("equal"); ax.set_title(name, fontsize=9); ax.tick_params(labelsize=7)
        fig.colorbar(pc, ax=ax, shrink=0.7).ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(names):]:
        ax.axis("off")
    fig.suptitle(f"South Florida, 4 km {SSP}, {LATE} monthly climatology (no overlays)", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "sfl_jan_panels.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
