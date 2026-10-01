"""
Annual forest (tree-PFT) area of the whole domain from the PFT-level h1 files,
for Figure 2 (historical regional series). One case per call.

    area_by_itype[year, t] = sum over PFTs of itype t of
                             pfts1d_wtgcell x gridcell area[km2] x landfrac       [km2]

so the tree area is the sum over itype 1-8 (the tree PFTs, as in
extract_elm_4km_tree_stemc.py), shrubs are itype 9-11, grasses 12-14, crops 15+,
bare ground itype 0. pfts1d_wtgcell is the weight stored in each year's h1 file
(it changes with land use). `land_area_km2` and `pft_area_ratio` (sum of all
PFT areas / land area, expected ~1) are saved so the weights can be checked.

h1 files are named by their first record's stamp (h1.2005-02-01 holds Jan-Dec
2005); the time_bounds are checked to span the calendar year. PFT weights are
read from the file as stored (one value per PFT, not time-varying within the
year in this output).

4 km h1 files are 7.5-12 GB but only the 1-D PFT index arrays are read. Must
run through Slurm:
    sbatch --export=NONE -J f2_forest code/submit_py.sbatch \
        code/figure2/extract_forest_area.py <case> <out.npz> [year_min year_max]
"""
import glob
import os
import re
import sys

import netCDF4
import numpy as np

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
NTYPE = 25  # itype 0..24 (ELM has 0 bare + 14 natural PFTs + crops; extra slots stay 0)
TREE = list(range(1, 9))


def year_of(path):
    return int(re.search(r"\.h1\.(\d+)-", os.path.basename(path)).group(1))


def main():
    case, out_npz = sys.argv[1], sys.argv[2]
    ymin = int(sys.argv[3]) if len(sys.argv) > 3 else -10**9
    ymax = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    run_dir = os.path.join(CASE_ROOT, case, "run")
    files = [f for f in sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h1.*.nc"))) if ymin <= year_of(f) <= ymax]
    assert files, f"no h1 files for {case} in [{ymin}, {ymax}]"
    years = [year_of(f) for f in files]
    assert years == list(range(years[0], years[0] + len(years))), f"years not consecutive: {years[:3]}...{years[-3:]}"

    area_by_type, land_area, ratio = [], [], []
    for f, year in zip(files, years):
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
            nlon = ds.dimensions["lon"].size
            cell_km2 = np.ma.filled(ds["area"][:], np.nan) * np.ma.filled(ds["landfrac"][:], np.nan)
            cell_km2 = np.where(np.isfinite(cell_km2), cell_km2, 0.0)
            itype = np.asarray(ds["pfts1d_itype_veg"][:]).astype(int)
            wt = np.ma.filled(ds["pfts1d_wtgcell"][:].astype("f8"), 0.0)
            wt = np.where(np.isfinite(wt), wt, 0.0)
            g = ((np.asarray(ds["pfts1d_jxy"][:]).astype(int) - 1) * nlon + (np.asarray(ds["pfts1d_ixy"][:]).astype(int) - 1))
        assert itype.max() < NTYPE, f"{year}: itype up to {itype.max()} exceeds {NTYPE - 1}"
        km2 = wt * cell_km2.ravel()[g]
        a = np.bincount(itype, weights=km2, minlength=NTYPE)
        area_by_type.append(a)
        land_area.append(float(cell_km2.sum()))
        ratio.append(float(a.sum() / cell_km2.sum()))
        print(f"{year}: tree area {a[TREE].sum():.0f} km2 ({100 * a[TREE].sum() / cell_km2.sum():.1f}% of land {cell_km2.sum():.0f} km2)  "
              f"PFT area / land area {ratio[-1]:.4f}", flush=True)

    area_by_type = np.array(area_by_type)
    meta = {"units": "km2",
            "definition": ("area_by_itype[year, t] = sum of pfts1d_wtgcell x area x landfrac over PFTs of itype t; "
                           "tree = itype 1-8, shrub 9-11, grass 12-14, crop 15+, bare 0"),
            "case": case, "run_dir": run_dir}
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), area_by_itype=area_by_type,
                            tree_area_km2=area_by_type[:, TREE].sum(axis=1),
                            land_area_km2=np.array(land_area), pft_area_ratio=np.array(ratio),
                            **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz}")


if __name__ == "__main__":
    main()
