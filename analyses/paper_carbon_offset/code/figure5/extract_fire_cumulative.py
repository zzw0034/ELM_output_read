"""
Cumulative complete-column fire carbon loss of one run, per gridcell, for the Figure 5 "benefit without fire
loss" (user decision 2026-10-01). One case per call, from the monthly h0 files.

Fire loss each year = NEP - LAND_USE_FLUX - NBP (the D4 identity, exact in this ELM version, notes 3.19;
COL_FIRE_CLOSS is not in h0), annual day-weighted mean of the monthly records, gC/m2/s -> gC/m2/yr.
Saved (float32, gC/m2 of gridcell land unless stated):
    fire_cum_endmean   mean over the end window [win0, win1] of the cumulative fire loss from year_min to each
                       year y, i.e. mean_y sum_{t=year_min..y} fire(t). Added to the window-mean stock difference
                       it gives the stock difference without fire loss over the same window.
    fire_cum_total     cumulative fire loss year_min..year_max
    fire_mean          mean annual fire loss over year_min..year_max (gC/m2/yr)
    fire_domain_PgC    annual domain total of fire loss (PgC/yr), one value per year
    TOTECOSYSC_mean    mean stock over year_min..year_max (gC/m2), for a whole-period fire-loss rate
plus year, lat, lon, area_km2 = area x landfrac. Adding back the fire loss is an approximation: carbon that did
not burn would partly have been respired later, and fire also changes stand dynamics.

Self-contained on purpose (do not import common.py). Must run through Slurm, from the analysis root:
    sbatch --export=NONE -J f5_fire code/submit_py.sbatch \\
        code/figure5/extract_fire_cumulative.py <case> <out.npz> <year_min> <year_max> <win0> <win1>
Output names expected by the Figure 5 plots:
    _cache/figure5/<res>/<SSP>[_RF]__firecum_2024-2100.npz
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
SEC_PER_YEAR = 365 * 86400.0
MONTH_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], dtype="f8")


def year_of(path):
    return int(re.search(r"\.h0\.(\d+)-", os.path.basename(path)).group(1))


def annual_mean(var, tb):
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
    ymin, ymax, w0, w1 = (int(v) for v in sys.argv[3:7])
    assert ymin <= w0 <= w1 <= ymax
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    run_dir = os.path.join(CASE_ROOT, case, "run")
    files = [f for f in sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h0.*.nc"))) if ymin <= year_of(f) <= ymax]
    years = [year_of(f) for f in files]
    assert years == list(range(ymin, ymax + 1)), f"{case}: need every year {ymin}-{ymax}, found {years[:3]}...{years[-3:]}"

    cum = endsum = stock = None
    domain = []
    lat = lon = area = None
    for f, year in zip(files, years):
        with netCDF4.Dataset(f) as ds:
            tb = np.ma.filled(ds["time_bounds"][:], np.nan)
            assert tb.shape[0] == 12 and np.allclose(tb[:, 1] - tb[:, 0], MONTH_DAYS), f"{os.path.basename(f)}: not 12 Jan-Dec months"
            y0 = int(ds["time"].units.split("since")[1].strip()[:4])
            lo, hi = 365 * (year - y0), 365 * (year - y0 + 1)
            assert abs(tb[0, 0] - lo) < 1.0 and abs(tb[-1, 1] - hi) < 1.0, f"{os.path.basename(f)}: time_bounds do not span {year}"
            cell = np.ma.filled(ds["area"][:], np.nan) * np.ma.filled(ds["landfrac"][:], np.nan)
            cell = np.where(np.isfinite(cell), cell, 0.0)
            if area is None:
                area, lat, lon = cell, np.asarray(ds["lat"][:]), np.asarray(ds["lon"][:])
            else:
                assert np.array_equal(cell, area), f"{year}: area x landfrac changed"
            v = {}
            for name in ("NEP", "LAND_USE_FLUX", "NBP"):
                assert ds[name].units.strip() == "gC/m^2/s", f"{name} units {ds[name].units}"
                v[name] = annual_mean(ds[name], tb) * SEC_PER_YEAR
            assert ds["TOTECOSYSC"].units.strip() == "gC/m^2"
            st = annual_mean(ds["TOTECOSYSC"], tb)
        fire = v["NEP"] - v["LAND_USE_FLUX"] - v["NBP"]
        cum = fire if cum is None else cum + fire
        stock = st if stock is None else stock + st
        if w0 <= year <= w1:
            endsum = cum.copy() if endsum is None else endsum + cum
        land = np.isfinite(fire) & (area > 0)
        domain.append(float((fire[land] * area[land]).sum() * 1e6 / 1e15))
        print(f"{year}: domain fire {domain[-1]:.4f} PgC/yr, peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.1f} GB", flush=True)

    n = len(years)
    out = {"fire_cum_endmean": (endsum / (w1 - w0 + 1)).astype("f4"), "fire_cum_total": cum.astype("f4"),
           "fire_mean": (cum / n).astype("f4"), "TOTECOSYSC_mean": (stock / n).astype("f4")}
    meta = {"units": "fire_cum_*: gC/m2; fire_mean: gC/m2/yr; fire_domain_PgC: PgC/yr; TOTECOSYSC_mean: gC/m2",
            "definition": f"fire = NEP - LAND_USE_FLUX - NBP (annual day-weighted means); cumulative from {ymin}; "
                          f"fire_cum_endmean = mean over {w0}-{w1} of the cumulative fire to each year",
            "case": case, "run_dir": run_dir}
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), lat=lat, lon=lon, area_km2=area,
                            fire_domain_PgC=np.array(domain), window=np.array([w0, w1], "i4"), **out,
                            **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}; cumulative domain fire {sum(domain):.3f} PgC over {ymin}-{ymax}")


if __name__ == "__main__":
    main()
