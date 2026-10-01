"""
Per-gridcell multi-year mean carbon-pool and flux maps of one run, for Figure 4
(pool contributions, three boundaries, restoration/protection strata), from the
monthly h0 files. One case per call.

For every h0 year in [year_min, year_max] and every variable the annual value is
the day-weighted mean of the 12 monthly records (time_bounds); the saved map is
the plain mean of those annual values (every year has 365 days, noleap).

    stocks  (gC/m2 of gridcell land):  TOTECOSYSC, TOTVEGC, TOTVEGC_ABG, CWDC,
                                       TOTLITC, TOTSOMC
    fluxes  (gC/m2/yr, converted from gC/m2/s):  NBP, NEP, LAND_USE_FLUX,
                                       WOOD_HARVESTC
    area_km2 = area x landfrac (land area per cell; 0 where no land)

TOTPRODC is not in h0; the plot script derives it as TOTECOSYSC - (TOTVEGC +
CWDC + TOTLITC + TOTSOMC), blueprint D4. The window must be complete: every
year in the range must exist and its time_bounds must span the calendar year.

Self-contained on purpose (the Pathfinder mirror is an rsync copy; do not import
common.py). Case names come from code/common.py (`FOURKM[...]`, `HALFDEG[...]`).
4 km h0 files are ~12 GB but only these 2-D variables are read. Must run through
Slurm, from the analysis root:
    sbatch --export=NONE -J f4_pools code/submit_py.sbatch \
        code/figure4/extract_pool_maps.py <case> <out.npz> <year_min> <year_max>
Output names expected by plot_pool_strata.py:
    _cache/figure4/<res>/<SSP>[_RF|_RH]__pools_<y0>-<y1>.npz
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
FLUXES = ["NBP", "NEP", "LAND_USE_FLUX", "WOOD_HARVESTC"]
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
    ymin, ymax = int(sys.argv[3]), int(sys.argv[4])
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    run_dir = os.path.join(CASE_ROOT, case, "run")
    files = [f for f in sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h0.*.nc"))) if ymin <= year_of(f) <= ymax]
    years = [year_of(f) for f in files]
    assert years == list(range(ymin, ymax + 1)), f"{case}: need every year {ymin}-{ymax}, found {years}"

    acc = {v: None for v in STOCKS + FLUXES}
    lat = lon = area = None
    for f, year in zip(files, years):
        with netCDF4.Dataset(f) as ds:
            tb = np.ma.filled(ds["time_bounds"][:], np.nan)
            y0 = int(ds["time"].units.split("since")[1].strip()[:4])
            lo, hi = 365 * (year - y0), 365 * (year - y0 + 1)
            assert abs(tb[0, 0] - lo) < 1.0 and abs(tb[-1, 1] - hi) < 1.0, \
                f"{os.path.basename(f)}: time_bounds {tb[0, 0]}-{tb[-1, 1]} do not span {year}"
            cell = np.ma.filled(ds["area"][:], np.nan) * np.ma.filled(ds["landfrac"][:], np.nan)
            cell = np.where(np.isfinite(cell), cell, 0.0)
            if area is None:
                area, lat, lon = cell, np.asarray(ds["lat"][:]), np.asarray(ds["lon"][:])
            else:
                assert np.array_equal(cell, area), f"{year}: area x landfrac changed between years"
            for v in STOCKS + FLUXES:
                unit = ds[v].units.strip()
                assert unit == ("gC/m^2" if v in STOCKS else "gC/m^2/s"), f"{v} units {unit}"
                a = annual_mean(ds[v], tb) * (1.0 if v in STOCKS else SEC_PER_YEAR)
                acc[v] = a if acc[v] is None else acc[v] + a
        print(f"{year}: read {len(STOCKS) + len(FLUXES)} variables, peak RSS "
              f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.1f} GB", flush=True)

    n = len(years)
    maps = {v: (acc[v] / n).astype("f4") for v in acc}
    land = area > 0
    for v in STOCKS:
        print(f"{v}: domain mean {np.nansum(maps[v][land] * area[land]) / area[land].sum():.1f} gC/m2 "
              f"(area-weighted), non-finite land cells {int((~np.isfinite(maps[v][land])).sum())}")
    meta = {"units": "stocks gC/m2; fluxes gC/m2/yr; area_km2 = area x landfrac",
            "definition": f"mean over {ymin}-{ymax} of the day-weighted annual means of the monthly h0 records",
            "case": case, "run_dir": run_dir}
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, lat=lat, lon=lon, area_km2=area, years=np.array(years, "i4"),
                            **maps, **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}")


if __name__ == "__main__":
    main()
