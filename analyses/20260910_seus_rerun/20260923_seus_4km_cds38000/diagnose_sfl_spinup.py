"""
When does the soil-carbon boundary at 80.73 W (south-east of Lake
Okeechobee, 25.4-26.9 N) form?

diagnose_sfl_edge81w.py found the future-run GPP/LAI boundary there is a soil
state boundary (TOTSOMC +5.6 kgC/m2 east, more mineral N) and that only two
inputs jump across it: surface-data FMAX (static) and the historical LUH2
harvest rate (0.25 deg, time-varying). If the TOTSOMC step already exists at
the end of the 1850 spin-ups (no harvest, fixed 1850 land cover), a static
input is responsible; if it only grows during the 1850-2023 transient, land
use / harvest history is.

Step metric: the boundary edges are at global edge index k = 342 / 343
(lon -80.75 / -80.708), so the step is taken between the column just west of
edge 342 (global column 341) and the column just east of edge 343 (global
column 343), row by row over 25.4-26.9 N:
   step = median over rows of (east - west)
   ratio = median |step| / median |two-column difference| elsewhere in the
           box (25.4-26.9 N, 81.5-80.2 W)
Stages: AD spin-up (all h0 files), final spin-up (all h0 files), transient
1850-2023 (annual means every 25 years + 2023), old Default future 2024 and
2100 (ssp585).

Run through Slurm:  sbatch -J sfl_spinup submit_py.sbatch diagnose_sfl_spinup.py
"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import OUTDIR, _read, _month_weights, case_name, load_grid

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
AD = "20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup"
FINAL = "20260911_Southeast_hires_20n_hdmfix_mapfix_ICB1850CNPRDCTCBC_final_spinup"
TRANS = "20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC"
FUT = case_name("Default", "ssp585")
TRANS_YEARS = [1850, 1875, 1900, 1925, 1950, 1975, 2000, 2023]
FUT_YEARS = [2024, 2100]
VARS = ["TOTSOMC", "SMINN", "TLAI", "GPP"]
ROW_LAT = (25.4, 26.9)
BOX_LON = (-81.5, -80.2)
COL_W, COL_E = 341, 343          # global columns either side of edges k=342/343


def read_stage(path, var):
    """Spin-up h0 files hold one ANNUAL record per model year (50 per AD file,
    44 per final spin-up file, 1 in the last file): use the last record, i.e.
    the final year of that file. Transient / future files hold 12 monthly
    records: day-weighted annual mean."""
    with Dataset(path) as ds:
        n = len(ds.dimensions["time"])
        if n == 12:
            return np.tensordot(_month_weights(ds), _read(ds, var), axes=(0, 0))
        tb = _read(ds, "time_bounds")
        if not np.allclose(tb[-1, 1] - tb[-1, 0], 365, atol=1e-6):
            raise RuntimeError(f"{path}: last record is not one year long")
        return np.ma.filled(ds.variables[var][n - 1].astype(float), np.nan)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid("ssp585")
    land = W > 0
    rows = np.where((lat >= ROW_LAT[0]) & (lat <= ROW_LAT[1]))[0]
    cols = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    assert abs(lon[COL_W] - (-80.7708)) < 1e-3 and abs(lon[COL_E] - (-80.6875)) < 1e-3, (lon[COL_W], lon[COL_E])

    stages = []
    for case, tag in ((AD, "AD spin-up"), (FINAL, "final spin-up")):
        for f in sorted(glob.glob(os.path.join(CASE_ROOT, case, "run", f"{case}.elm.h0.*.nc"))):
            with Dataset(f) as ds:
                last_year = int(round(float(ds.variables["time_bounds"][-1, 0]) / 365)) + 1
            stages.append((f"{tag} yr {last_year}", f))
    for y in TRANS_YEARS:
        stages.append((f"transient {y}", os.path.join(CASE_ROOT, TRANS, "run", f"{TRANS}.elm.h0.{y}-02-01-00000.nc")))
    for y in FUT_YEARS:
        stages.append((f"Default ssp585 {y}", os.path.join(CASE_ROOT, FUT, "run", f"{FUT}.elm.h0.{y}-02-01-00000.nc")))

    lines = ["Step across the 80.73 W boundary (east column 343 minus west column 341), rows "
             f"{ROW_LAT[0]}-{ROW_LAT[1]}N; ratio = |step| / typical two-column difference in the box",
             f"{'stage':28s}" + "".join(f"{v + ' step':>16s}{'ratio':>7s}" for v in VARS)]
    profiles = {}
    maps = {}
    for label, path in stages:
        if not os.path.exists(path):
            lines.append(f"{label:28s}  MISSING {path}")
            continue
        line = f"{label:28s}"
        for v in VARS:
            f = np.where(land, read_stage(path, v), np.nan)
            step = f[rows, COL_E] - f[rows, COL_W]
            blk = f[np.ix_(rows, cols)]
            two = np.abs(blk[:, 2:] - blk[:, :-2])
            typ = np.nanmedian(two)
            ratio = np.nanmedian(np.abs(step)) / typ if typ > 0 else np.nan
            line += f"{np.nanmedian(step):16.4g}{ratio:7.1f}"
            if v == "TOTSOMC":
                profiles[label] = np.nanmean(blk, axis=0)
                maps[label] = f
        lines.append(line)
        print(line, flush=True)
    txt = "\n".join(lines)
    with open(os.path.join(OUTDIR, "sfl_spinup_summary.txt"), "w") as fh:
        fh.write(txt + "\n")
    print(txt)

    # longitude profile of TOTSOMC averaged over the rows
    fig, ax = plt.subplots(figsize=(11, 6))
    cmap = plt.get_cmap("viridis")
    labels = list(profiles)
    for n, lab in enumerate(labels):
        ax.plot(lon[cols], profiles[lab] / 1000, color=cmap(n / max(len(labels) - 1, 1)), lw=1.2, label=lab)
    ax.axvline(-80.73, color="gray", ls=":", lw=1)
    ax.set_xlabel("longitude"); ax.set_ylabel("TOTSOMC (kgC m$^{-2}$), mean over 25.4-26.9N")
    ax.set_title("Soil organic carbon across the 80.73W boundary, by stage (dotted = boundary)")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "sfl_spinup_totsomc_profile.png"), dpi=150)
    plt.close(fig)

    # maps, SE of Lake Okeechobee, no overlays
    pick = [l for l in labels if l.startswith("AD")][-1:] + [l for l in labels if l.startswith("final")][-1:] + \
           [l for l in labels if l.startswith("transient") and l.split()[-1] in ("1850", "1950", "2023")] + \
           [l for l in labels if l.endswith("2100")]
    jj = np.where((lat >= 25.3) & (lat <= 27.2))[0]; ii = np.where((lon >= -81.8) & (lon <= -80.0))[0]
    vmax = np.nanpercentile(np.concatenate([maps[p][np.ix_(jj, ii)].ravel() for p in pick]), 99)
    fig, axes = plt.subplots(1, len(pick), figsize=(4.2 * len(pick), 5))
    for ax, p in zip(np.atleast_1d(axes), pick):
        pc = ax.pcolormesh(lon[ii], lat[jj], maps[p][np.ix_(jj, ii)] / 1000, cmap="viridis",
                           vmin=0, vmax=vmax / 1000, shading="nearest")
        ax.set_aspect("equal"); ax.set_title(p, fontsize=10); ax.tick_params(labelsize=7)
    fig.colorbar(pc, ax=list(np.atleast_1d(axes)), shrink=0.8, label="TOTSOMC (kgC m$^{-2}$)")
    fig.suptitle("TOTSOMC south-east of Lake Okeechobee by stage (no overlays)", fontsize=12)
    fig.savefig(os.path.join(OUTDIR, "sfl_spinup_totsomc_maps.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)
    print("wrote figures")


if __name__ == "__main__":
    main()
