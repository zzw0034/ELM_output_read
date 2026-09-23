"""
Does the HISTORICAL forcing (used by the spin-ups and the 1850-2023
transient) jump across the 80.73 W boundary south-east of Lake Okeechobee?

diagnose_sfl_spinup.py showed the vegetation/soil boundary there already
exists in year 49 of the AD spin-up (fixed 1850 land cover, no harvest), and
no surface-data field or PFT fraction steps systematically across it. The
future forcing was checked before; the spin-ups cycle a different dataset
(TESSFA2 Daymet-ERA5 1980-2023), which is checked here through the forcing
diagnostics the transient run itself wrote (TBOT, RAIN, SNOW, FSDS, FLDS,
QBOT, WIND, PBOT), 2014-2023 mean.

For each variable, row by row over 25.4-26.9 N: step = east column 343 minus
west column 341; reports the median step, the share of rows where it has the
same sign as the median, and the median |two-column difference| elsewhere in
25.4-26.9 N, 81.5-80.2 W for scale. Also a longitude profile (row mean) of
each variable across 81.5-80.2 W, with the future (oldDF, 2091-2100) forcing
for comparison.

Run through Slurm:  sbatch -J sfl_forc submit_py.sbatch diagnose_sfl_forcing_hist.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import OUTDIR, PERIODS, LATE, _read, _month_weights, case_name, h0_climatology, load_grid

TRANS = "20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC"
CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
YEARS = range(2014, 2024)
VARS = ["TBOT", "RAIN", "SNOW", "FSDS", "FLDS", "QBOT", "WIND", "PBOT", "TLAI"]
ROW_LAT = (25.4, 26.9)
BOX_LON = (-81.5, -80.2)
COL_W, COL_E = 341, 343


def trans_mean(var):
    acc = []
    for y in YEARS:
        with Dataset(os.path.join(CASE_ROOT, TRANS, "run", f"{TRANS}.elm.h0.{y}-02-01-00000.nc")) as ds:
            acc.append(np.tensordot(_month_weights(ds), _read(ds, var), axes=(0, 0)))
    return np.nanmean(acc, axis=0)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid("ssp585")
    land = W > 0
    rows = np.where((lat >= ROW_LAT[0]) & (lat <= ROW_LAT[1]))[0]
    cols = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    fut = case_name("oldDF", "ssp585")
    lines = [f"Across 80.73 W (col {COL_E} - col {COL_W}), rows {ROW_LAT[0]}-{ROW_LAT[1]}N",
             f"{'var':6s}{'period':>12s}{'median step':>14s}{'same sign':>11s}{'typical |2-col d|':>19s}{'ratio':>8s}"]
    prof = {}
    for v in VARS:
        for tag, fld in (("2014-2023", trans_mean(v)), (LATE + " DF", h0_climatology(fut, v, PERIODS[LATE])[0])):
            f = np.where(land, fld, np.nan)
            step = f[rows, COL_E] - f[rows, COL_W]
            med = np.nanmedian(step)
            same = np.nanmean(np.sign(step) == np.sign(med)) if med != 0 else np.nan
            blk = f[np.ix_(rows, cols)]
            typ = np.nanmedian(np.abs(blk[:, 2:] - blk[:, :-2]))
            ratio = abs(med) / typ if typ > 0 else np.nan
            lines.append(f"{v:6s}{tag:>12s}{med:14.4g}{same:11.2f}{typ:19.4g}{ratio:8.2f}")
            prof[(v, tag)] = np.nanmean(blk, axis=0)
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUTDIR, "sfl_forcing_hist_summary.txt"), "w") as fh:
        fh.write(txt + "\n")

    fig, axes = plt.subplots(3, 3, figsize=(16, 11))
    for ax, v in zip(axes.flat, VARS):
        for tag, st in (("2014-2023", "-"), (LATE + " DF", "--")):
            ax.plot(lon[cols], prof[(v, tag)], st, marker=".", ms=3, label=f"{tag}")
        ax.axvline(-80.73, color="gray", ls=":", lw=1)
        ax.set_title(f"{v}, row mean {ROW_LAT[0]}-{ROW_LAT[1]}N", fontsize=10)
        ax.tick_params(labelsize=8)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("Forcing across the 80.73W boundary (dotted): historical (transient 2014-2023) vs future", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "sfl_forcing_hist_profiles.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
