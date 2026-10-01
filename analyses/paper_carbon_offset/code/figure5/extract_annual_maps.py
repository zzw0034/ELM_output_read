"""
Per-gridcell annual maps of one run, for the Figure 5 risk components (blueprint D7, D9),
from the monthly h0 files. One case per call.

For every year in [year_min, year_max] (all must exist; time_bounds must span the year and
hold 12 monthly records, January first):
    NBP, NEP, LAND_USE_FLUX   annual day-weighted mean, converted gC/m2/s -> gC/m2/yr
    TOTECOSYSC                annual day-weighted mean stock, gC/m2
    BTRAN_GS                  growing-season (April-October, records 4-10) day-weighted mean of
                              BTRAN (unitless; user decision 2026-10-01: fixed April-October)
Saved as float32 arrays (year, lat, lon) with lat, lon, area_km2 = area x landfrac.

Used for: fire = NEP - LAND_USE_FLUX - NBP (complete column fire loss from the D4 identity,
COL_FIRE_CLOSS is not in h0) divided by TOTECOSYSC; water stress = 1 - BTRAN_GS; carbon
variability = detrended interannual SD of NBP.

Self-contained on purpose (do not import common.py). Must run through Slurm, from the
analysis root:
    sbatch --export=NONE -J f5_ann code/submit_py.sbatch \\
        code/figure5/extract_annual_maps.py <case> <out.npz> <year_min> <year_max>
Output names expected by plot_priority_selection.py:
    _cache/figure5/<res>/<SSP>[_RF]__annual_<y0>-<y1>.npz
(PF_CASE_ROOT overrides the case root, for the synthetic test only.)
"""
import glob
import os
import re
import resource
import sys

import netCDF4
import numpy as np

CASE_ROOT = os.environ.get("PF_CASE_ROOT", "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun")
FLUXES = ["NBP", "NEP", "LAND_USE_FLUX"]
STOCKS = ["TOTECOSYSC"]
GS_RECORDS = slice(3, 10)        # April-October of a January-first monthly file
SEC_PER_YEAR = 365 * 86400.0     # noleap calendar
MONTH_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], dtype="f8")


def year_of(path):
    return int(re.search(r"\.h0\.(\d+)-", os.path.basename(path)).group(1))


def weighted_mean(var, tb, sel=slice(None)):
    """Day-weighted mean over the selected monthly records; NaN where no selected month is finite."""
    vals = np.ma.filled(var[sel].astype("f8"), np.nan)
    w = (tb[sel, 1] - tb[sel, 0]).astype("f8")
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

    out = {v: [] for v in FLUXES + STOCKS + ["BTRAN_GS"]}
    lat = lon = area = None
    for f, year in zip(files, years):
        with netCDF4.Dataset(f) as ds:
            tb = np.ma.filled(ds["time_bounds"][:], np.nan)
            assert tb.shape[0] == 12, f"{os.path.basename(f)}: {tb.shape[0]} records, expected 12 monthly"
            assert np.allclose(tb[:, 1] - tb[:, 0], MONTH_DAYS), f"{os.path.basename(f)}: records are not Jan-Dec months"
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
            for v in FLUXES + STOCKS:
                unit = ds[v].units.strip()
                assert unit == ("gC/m^2/s" if v in FLUXES else "gC/m^2"), f"{v} units {unit}"
                out[v].append((weighted_mean(ds[v], tb) * (SEC_PER_YEAR if v in FLUXES else 1.0)).astype("f4"))
            assert ds["BTRAN"].units.strip() == "1", f"BTRAN units {ds['BTRAN'].units}"
            out["BTRAN_GS"].append(weighted_mean(ds["BTRAN"], tb, GS_RECORDS).astype("f4"))
        print(f"{year}: done, peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.1f} GB", flush=True)

    arrays = {k: np.stack(v) for k, v in out.items()}
    land = area > 0
    fire = arrays["NEP"] - arrays["LAND_USE_FLUX"] - arrays["NBP"]
    print(f"area-weighted means over land, {ymin}-{ymax}: NBP {np.nansum(arrays['NBP'].mean(0)[land] * area[land]) / area[land].sum():.2f} gC/m2/yr; "
          f"implied fire {np.nansum(fire.mean(0)[land] * area[land]) / area[land].sum():.2f} gC/m2/yr; "
          f"1-BTRAN_GS {np.nansum((1 - arrays['BTRAN_GS'].mean(0))[land] * area[land]) / area[land].sum():.3f}; "
          f"non-finite land cells in BTRAN_GS {int((~np.isfinite(arrays['BTRAN_GS'].mean(0)[land])).sum())}")
    meta = {"units": "NBP, NEP, LAND_USE_FLUX gC/m2/yr; TOTECOSYSC gC/m2; BTRAN_GS 1; area_km2 = area x landfrac",
            "definition": "annual day-weighted means of the monthly h0 records; BTRAN_GS = April-October day-weighted mean",
            "case": case, "run_dir": run_dir}
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), lat=lat, lon=lon, area_km2=area, **arrays,
                            **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}")


if __name__ == "__main__":
    main()
