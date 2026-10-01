"""
ELM soil organic carbon to 1 m (`TOTSOMC_1m`) for Figure 4, from the monthly h0
files of one run. One case per call. Gives both
  * the annual domain total [PgC], every year in [year_min, year_max]
    (the 2024-2100 pool trajectories), and
  * the mean map over [map_min, map_max] [gC/m2] (the 2091-2100 maps, the strata).

TOTSOMC_1m is the model's own 0-100 cm soil-pool carbon (SOIL1-4C_vr; litter and CWD
are separate), layers fully above 1 m counted whole and the straddling layer by the share
of its thickness above 1 m. It equals the overlap integral of SOIL1-4C_vr to 1 m
(checked at both resolutions, notes 3.4). `TOTSOMC` used in notes 3.10-3.12 is the whole
soil column (about 35 % of it lies below 1 m), so the soil below 1 m is
TOTSOMC - TOTSOMC_1m.

Each year is the day-weighted mean of the 12 monthly records (time_bounds); the
bounds must span the calendar year, every year of the range must exist. Domain total =
sum over land cells of field[gC/m2] x area x landfrac x 1e6 / 1e15 over cells with a
finite value and area x landfrac > 0.

Self-contained on purpose (do not import common.py). Must run through Slurm, from the
analysis root:
    sbatch --export=NONE -J f4_soc1m code/submit_py.sbatch \\
        code/figure4/extract_soc1m.py <case> <out.npz> <year_min> <year_max> <map_min> <map_max>
Output names expected by the Figure 4 plots:
    _cache/figure4/4km/<SSP>[_RF|_RH]__soc1m_2024-2100.npz
(PF_CASE_ROOT overrides the case root, for the synthetic test only.)
"""
import glob
import os
import re
import sys

import netCDF4
import numpy as np

CASE_ROOT = os.environ.get("PF_CASE_ROOT", "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun")
VAR = "TOTSOMC_1m"


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
    ymin, ymax, mmin, mmax = (int(a) for a in sys.argv[3:7])
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    assert ymin <= mmin <= mmax <= ymax
    run_dir = os.path.join(CASE_ROOT, case, "run")
    files = [f for f in sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h0.*.nc"))) if ymin <= year_of(f) <= ymax]
    years = [year_of(f) for f in files]
    assert years == list(range(ymin, ymax + 1)), f"{case}: need every year {ymin}-{ymax}, found {years[:3]}...{years[-3:]}"

    totals, acc, n_map = [], None, 0
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
            unit = ds[VAR].units.strip()
            assert unit == "gC/m^2", f"{VAR} units {unit}"
            a = annual_mean(ds[VAR], tb)
        m = np.isfinite(a) & (area > 0)
        totals.append(float((a[m] * area[m]).sum() * 1e6 / 1e15))
        if mmin <= year <= mmax:
            acc = a if acc is None else acc + a
            n_map += 1
        print(f"{year}: {VAR} domain total {totals[-1]:.4f} PgC over {int(m.sum())} cells", flush=True)

    assert n_map == mmax - mmin + 1
    mean_map = (acc / n_map).astype("f4")
    meta = {"units": "total_PgC: PgC; mean_map: gC/m2; area_km2 = area x landfrac",
            "definition": f"{VAR}: day-weighted annual means; mean_map is the mean over {mmin}-{mmax}",
            "case": case, "run_dir": run_dir}
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), total_PgC=np.array(totals), mean_map=mean_map,
                            map_years=np.array([mmin, mmax], "i4"), lat=lat, lon=lon, area_km2=area,
                            **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}")


if __name__ == "__main__":
    main()
