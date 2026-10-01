"""
Annual domain totals of ELM carbon stocks and net fluxes for Figure 2 /
Results 3.2 (regional trajectories and paired management benefits), one case
per call, from the monthly h0 files.

For every h0 year (day-weighted mean of the 12 monthly records, time_bounds)
and every variable, the domain total is
    sum_cells  field[gC/m2 (or gC/m2/yr)] x area[km2] x landfrac x 1e6 / 1e15   [PgC (or PgC/yr)]
over land cells (area x landfrac > 0, finite field).

Stocks (annual mean of the monthly stock): TOTECOSYSC, TOTVEGC, TOTVEGC_ABG,
CWDC, TOTLITC, TOTSOMC. `prod_resid` = TOTECOSYSC - (TOTVEGC+CWDC+TOTLITC+TOTSOMC)
is the product-pool term (TOTPRODC is not in h0, blueprint D4): it should be
~0 early in the transient and positive where wood products accumulate. The
h0 long_name of TOTECOSYSC says "excl product pools" while ColumnDataType.F90
sums TOTPRODC into it; the residual decides, so it is saved, not assumed.
Fluxes (gC/m2/s x 365 x 86400 -> per year): GPP, NBP, WOOD_HARVESTC, LAND_USE_FLUX.

Self-contained on purpose (the Pathfinder mirror is an rsync copy; do not
import common.py). 4 km h0 files are ~12 GB but only these 2-D variables are
read. Must run through Slurm:
    sbatch --export=NONE -J f2_<tag> code/submit_py.sbatch \
        code/figure2/extract_domain_totals.py <case> <out.npz> [year_min year_max]
Default years: every h0 file of the case.
"""
import glob
import os
import re
import resource
import sys

import netCDF4
import numpy as np

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
STOCKS = ["TOTECOSYSC", "TOTVEGC", "TOTVEGC_ABG", "CWDC", "TOTLITC", "TOTSOMC"]
FLUXES = ["GPP", "NBP", "WOOD_HARVESTC", "LAND_USE_FLUX"]
SEC_PER_YEAR = 365 * 86400.0  # noleap calendar


def year_of(path):
    return int(re.search(r"\.h0\.(\d+)-", os.path.basename(path)).group(1))


def annual_mean(var, tb):
    """Day-weighted mean over time of a (time, lat, lon) variable; NaN where no month is finite."""
    vals = np.ma.filled(var[:].astype("f8"), np.nan)
    w = (tb[:, 1] - tb[:, 0]).astype("f8")
    fin = np.isfinite(vals)
    wm = np.where(fin, w[:, None, None], 0.0)
    ws = wm.sum(axis=0)
    out = np.full(vals.shape[1:], np.nan)
    ok = ws > 0
    out[ok] = (np.where(fin, vals, 0.0) * wm).sum(axis=0)[ok] / ws[ok]
    return out


def main():
    case, out_npz = sys.argv[1], sys.argv[2]
    ymin = int(sys.argv[3]) if len(sys.argv) > 3 else -10**9
    ymax = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    run_dir = os.path.join(CASE_ROOT, case, "run")
    files = [f for f in sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h0.*.nc"))) if ymin <= year_of(f) <= ymax]
    assert files, f"no h0 files for {case} in [{ymin}, {ymax}]"
    years = [year_of(f) for f in files]
    assert years == list(range(years[0], years[0] + len(years))), f"years not consecutive: {years[:3]}...{years[-3:]}"

    out = {v: [] for v in STOCKS + FLUXES}
    land_area = []
    for f in files:
        year = year_of(f)
        with netCDF4.Dataset(f) as ds:
            tb = np.ma.filled(ds["time_bounds"][:], np.nan)
            y0 = int(ds["time"].units.split("since")[1].strip()[:4])
            lo, hi = 365 * (year - y0), 365 * (year - y0 + 1)
            # The very first record of a run starts one model time step early
            # (1850 file: -1/24 d), so allow < 1 day of slack, and say so.
            assert abs(tb[0, 0] - lo) < 1.0 and abs(tb[-1, 1] - hi) < 1.0, \
                f"{os.path.basename(f)}: time_bounds {tb[0, 0]}-{tb[-1, 1]} do not span {year}"
            if (tb[0, 0], tb[-1, 1]) != (lo, hi):
                print(f"  note: {year} time_bounds {tb[0, 0]:.4f}-{tb[-1, 1]:.4f} d (expected {lo}-{hi}); weights used as stored", flush=True)
            w = np.ma.filled(ds["area"][:], np.nan) * np.ma.filled(ds["landfrac"][:], np.nan)  # km2 land
            w = np.where(np.isfinite(w), w, 0.0)
            land_area.append(float(w.sum()))
            for v in STOCKS + FLUXES:
                unit = ds[v].units.strip()
                assert unit == ("gC/m^2" if v in STOCKS else "gC/m^2/s"), f"{v} units {unit}"
                a = annual_mean(ds[v], tb) * (1.0 if v in STOCKS else SEC_PER_YEAR)
                m = np.isfinite(a) & (w > 0)
                out[v].append(float((a[m] * w[m]).sum() * 1e6 / 1e15))
        print(f"{year}: TOTECOSYSC {out['TOTECOSYSC'][-1]:.4f} PgC  TOTVEGC {out['TOTVEGC'][-1]:.4f}  "
              f"NBP {out['NBP'][-1]:+.4f} PgC/yr  land {land_area[-1] / 1e6:.4f} Mkm2  "
              f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.1f} GB", flush=True)

    arrays = {k: np.array(v, "f8") for k, v in out.items()}
    arrays["prod_resid"] = arrays["TOTECOSYSC"] - (arrays["TOTVEGC"] + arrays["CWDC"] + arrays["TOTLITC"] + arrays["TOTSOMC"])
    meta = {"units": "stocks and prod_resid: PgC (annual mean of monthly stock); fluxes: PgC per year; land_area_km2: km2",
            "definition": ("domain total = sum over land cells of annual day-weighted mean x area x landfrac; "
                           "prod_resid = TOTECOSYSC - (TOTVEGC + CWDC + TOTLITC + TOTSOMC)"),
            "case": case, "run_dir": run_dir}
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), land_area_km2=np.array(land_area), **arrays,
                            **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}; prod_resid first/last: {arrays['prod_resid'][0]:+.5f} / {arrays['prod_resid'][-1]:+.5f} PgC")


if __name__ == "__main__":
    main()
