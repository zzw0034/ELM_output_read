"""
Per-gridcell PFT area fractions of one run in one year, from the PFT-level h1
file, for the Figure 4 restoration/protection strata (blueprint E4).

    tree_frac[j, i]  = sum of pfts1d_wtgcell over PFTs of itype 1-8   (fraction of gridcell land)
    grass_frac       = itype 12-14,  shrub_frac = itype 9-11,  crop_frac = itype 15+
    pft_ratio        = sum of all PFT weights (expected ~1, saved so it can be checked)

The strata are defined from the land cover the RF prescription adds: the
increment is RF-run tree_frac in a plateau year (RF holds its land cover fixed
after 2049, notes §3.9) minus the 2023 tree_frac of the transient run that
the future runs restart from. The increment is the same in every SSP by design,
so it does not depend on the SSP's own land-use drift, and it is fixed before
any carbon benefit is looked at.

Self-contained on purpose (do not import common.py). 4 km h1 files are 7.5-12 GB
but only the 1-D PFT index arrays are read. Must run through Slurm, from the
analysis root:
    sbatch --export=NONE -J f4_tree code/submit_py.sbatch \
        code/figure4/extract_tree_fraction.py <case> <year> <out.npz>
Output names expected by plot_pool_strata.py:
    _cache/figure4/<res>/transient__treefrac_2023.npz
    _cache/figure4/<res>/<SSP>_RF__treefrac_<year>.npz
"""
import glob
import os
import re
import sys

import netCDF4
import numpy as np

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
TREE, SHRUB, GRASS = range(1, 9), range(9, 12), range(12, 15)
CROP_MIN = 15


def year_of(path):
    return int(re.search(r"\.h1\.(\d+)-", os.path.basename(path)).group(1))


def main():
    case, year, out_npz = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    run_dir = os.path.join(CASE_ROOT, case, "run")
    files = [f for f in sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h1.*.nc"))) if year_of(f) == year]
    assert len(files) == 1, f"{case}: expected one h1 file for {year}, found {files}"
    with netCDF4.Dataset(files[0]) as ds:
        tb = np.ma.filled(ds["time_bounds"][:], np.nan)
        y0 = int(ds["time"].units.split("since")[1].strip()[:4])
        lo, hi = 365 * (year - y0), 365 * (year - y0 + 1)
        assert abs(tb[0, 0] - lo) < 1.0 and abs(tb[-1, 1] - hi) < 1.0, \
            f"{os.path.basename(files[0])}: time_bounds {tb[0, 0]}-{tb[-1, 1]} do not span {year}"
        nlat, nlon = ds.dimensions["lat"].size, ds.dimensions["lon"].size
        lat, lon = np.asarray(ds["lat"][:]), np.asarray(ds["lon"][:])
        cell = np.ma.filled(ds["area"][:], np.nan) * np.ma.filled(ds["landfrac"][:], np.nan)
        cell = np.where(np.isfinite(cell), cell, 0.0)
        itype = np.asarray(ds["pfts1d_itype_veg"][:]).astype(int)
        wt = np.ma.filled(ds["pfts1d_wtgcell"][:].astype("f8"), 0.0)
        wt = np.where(np.isfinite(wt), wt, 0.0)
        g = (np.asarray(ds["pfts1d_jxy"][:]).astype(int) - 1) * nlon + (np.asarray(ds["pfts1d_ixy"][:]).astype(int) - 1)

    def frac(sel):
        return np.bincount(g[sel], weights=wt[sel], minlength=nlat * nlon).reshape(nlat, nlon).astype("f4")

    out = {"tree_frac": frac(np.isin(itype, list(TREE))), "shrub_frac": frac(np.isin(itype, list(SHRUB))),
           "grass_frac": frac(np.isin(itype, list(GRASS))), "crop_frac": frac(itype >= CROP_MIN),
           "pft_ratio": frac(np.ones_like(itype, dtype=bool))}
    land = cell > 0
    print(f"{case} {year}: tree area {(out['tree_frac'][land] * cell[land]).sum():.0f} km2 of land "
          f"{cell.sum():.0f} km2; PFT-weight sum over land cells: min {out['pft_ratio'][land].min():.4f} "
          f"max {out['pft_ratio'][land].max():.4f}")
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, lat=lat, lon=lon, area_km2=cell, year=np.int32(year), **out,
                            case=np.array(case), run_dir=np.array(run_dir),
                            definition=np.array("fractions of gridcell land: sum pfts1d_wtgcell by itype; tree 1-8, shrub 9-11, grass 12-14, crop 15+"))
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}")


if __name__ == "__main__":
    main()
