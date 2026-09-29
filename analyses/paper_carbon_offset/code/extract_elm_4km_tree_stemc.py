"""
Extract the ELM quantity that matches the ESA CCI Biomass AGB definition
(oven-dry woody AGB of *trees*, per unit area of the whole pixel): tree-PFT
stem carbon, LIVESTEMC + DEADSTEMC summed over PFT itypes 1-8 and weighted
by each PFT's gridcell fraction (pfts1d_wtgcell), so non-tree land
contributes zero and the value is per unit gridcell land area.

    tree_stemc(g) = sum_{p in g, itype 1..8} (LIVESTEMC_p + DEADSTEMC_p) * wtgcell_p

Shrub stems (itypes 9-11) are written separately as shrub_stemc; they are
not part of the ESA tree definition. Leaves and coarse roots are excluded.
Each year is a day-weighted annual mean of the monthly h1 records
(time_bounds), taken per PFT before the gridcell sum.

Default years are the ESA CCI v7.0 epochs that fall inside the 1850-2023
transient: 2005-2012 and 2015-2023 (ESA has no 2013-2014 maps; 2024 would
come from the future runs).

Self-contained on purpose: the Pathfinder mirror of this folder is an rsync
copy in an older layout, so it does not import code/common.py.

Must run through Slurm (4 km h1 files are 7.5-12 GB with ~2.44M PFTs):
    sbatch --export=NONE -J tree_stemc code/submit_py.sbatch \
        code/extract_elm_4km_tree_stemc.py <case> <out.npz> [year ...]
"""
import gc
import glob
import os
import resource
import sys
import warnings

import netCDF4
import numpy as np

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
DEFAULT_YEARS = list(range(2005, 2013)) + list(range(2015, 2024))
TREE_TYPES = list(range(1, 9))
TREE = set(TREE_TYPES)
SHRUB = {9, 10, 11}
STEM_VARS = ["LIVESTEMC", "DEADSTEMC"]


def h1_file(run_dir, case, year):
    files = sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h1.{year:04d}-*.nc")))
    assert len(files) == 1, f"expected one h1 file for {year}, found {files}"
    return files[0]


def annual_mean(var, tb):
    """Day-weighted mean over time of a (time, pft) variable; NaN-aware."""
    vals = np.ma.filled(var[:].astype("f8"), np.nan)
    if vals.shape[0] == 1:
        return vals[0]
    if tb is None:
        warnings.warn("no time_bounds; unweighted mean over time", RuntimeWarning)
        return np.nanmean(vals, axis=0)
    w = (tb[:, 1] - tb[:, 0]).astype("f8")
    fin = np.isfinite(vals)
    wm = np.where(fin, w[:, None], 0.0)
    ws = wm.sum(axis=0)
    out = np.full(vals.shape[1], np.nan)
    ok = ws > 0
    out[ok] = (np.where(fin, vals, 0.0) * wm).sum(axis=0)[ok] / ws[ok]
    return out


def main():
    case, out_nc = sys.argv[1], sys.argv[2]
    years = [int(y) for y in sys.argv[3:]] or DEFAULT_YEARS
    run_dir = os.path.join(CASE_ROOT, case, "run")
    assert not os.path.exists(out_nc), f"{out_nc} exists; refusing to overwrite"

    maps = {k: [] for k in ["tree_stemc", "shrub_stemc", "tree_frac", "veg_frac",
                            "stemc_dens_by_type", "frac_by_type"]}
    lat = lon = landfrac = area = None
    for year in years:
        f = h1_file(run_dir, case, year)
        ds = netCDF4.Dataset(f)
        for v in STEM_VARS:
            assert v in ds.variables, f"{v} not in {os.path.basename(f)}"
        if lat is None:
            lat, lon = ds["lat"][:].filled(np.nan), ds["lon"][:].filled(np.nan)
            landfrac = ds["landfrac"][:].filled(np.nan)
            area = ds["area"][:].filled(np.nan)
            units = ds["LIVESTEMC"].units
            assert units.strip() == "gC/m^2", units
        nlat, nlon = lat.size, lon.size
        itype = np.asarray(ds["pfts1d_itype_veg"][:]).astype(int)
        wt = np.ma.filled(ds["pfts1d_wtgcell"][:].astype("f8"), 0.0)
        wt = np.where(np.isfinite(wt), wt, 0.0)
        g = ((np.asarray(ds["pfts1d_jxy"][:]).astype(int) - 1) * nlon
             + (np.asarray(ds["pfts1d_ixy"][:]).astype(int) - 1))
        tb = np.ma.filled(ds["time_bounds"][:], np.nan)
        # h1 files are named by their first record's stamp (h1.2005-02-01 holds
        # Jan-Dec 2005); check the bounds really span this calendar year.
        y0 = int(ds["time"].units.split("since")[1].strip()[:4])
        assert (tb[0, 0], tb[-1, 1]) == (365 * (year - y0), 365 * (year - y0 + 1)), \
            f"{os.path.basename(f)} time_bounds {tb[0, 0]}-{tb[-1, 1]} do not span {year}"
        stem = sum(annual_mean(ds[v], tb) for v in STEM_VARS)
        ntime = ds.dimensions["time"].size
        ds.close()

        is_tree = np.isin(itype, list(TREE)) & (wt > 0)
        is_shrub = np.isin(itype, list(SHRUB)) & (wt > 0)
        bad = is_tree & ~np.isfinite(stem)
        assert not bad.any(), f"{year}: {bad.sum()} weighted tree PFTs have non-finite stem C"
        stem0 = np.where(np.isfinite(stem), stem, 0.0)

        def gsum(mask, values):
            return np.bincount(g[mask], weights=values[mask], minlength=nlat * nlon).reshape(nlat, nlon)

        veg = gsum(wt > 0, wt)
        has = veg > 0
        for key, mask, vals in [("tree_stemc", is_tree, stem0 * wt), ("shrub_stemc", is_shrub, stem0 * wt),
                                ("tree_frac", is_tree, wt), ("veg_frac", wt > 0, wt)]:
            maps[key].append(np.where(has, gsum(mask, vals), np.nan))
        # Per tree type: stem C per unit area of that type (density) and its
        # gridcell fraction, for the land-cover-downscaled comparator
        # B(i) = sum_t density_t(0.5 deg parent) * frac_t(4 km cell).
        dens_t, frac_t = [], []
        for t in TREE_TYPES:
            m = (itype == t) & (wt > 0)
            fw = gsum(m, wt)
            with np.errstate(invalid="ignore", divide="ignore"):
                dens_t.append(np.where(fw > 0, gsum(m, stem0 * wt) / fw, np.nan))
            frac_t.append(np.where(has, fw, np.nan))
        recon = np.nansum(np.stack(dens_t) * np.nan_to_num(np.stack(frac_t)), axis=0)
        ok = np.isfinite(maps["tree_stemc"][-1])
        assert np.allclose(recon[ok], maps["tree_stemc"][-1][ok], rtol=1e-6, atol=1e-3), \
            f"{year}: sum_t density*fraction does not reproduce tree_stemc"
        maps["stemc_dens_by_type"].append(np.stack(dens_t))
        maps["frac_by_type"].append(np.stack(frac_t))
        tm = maps["tree_stemc"][-1]
        tbr = f"time_bounds {tb[0, 0]:.0f}-{tb[-1, 1]:.0f} d"
        n_tree, n_cells = int(is_tree.sum()), int(has.sum())
        # Free the per-PFT arrays and log peak RSS. (Jobs 596645/596680 were
        # first blamed on memory; the real cause was the exceeded scratch
        # project quota, see analysis_process_notes §3.2.)
        del itype, wt, g, stem, stem0, is_tree, is_shrub, bad, veg, has, dens_t, frac_t
        gc.collect()
        rss_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
        print(f"{year}: {os.path.basename(f)} ntime={ntime} {tbr} tree PFTs={n_tree} "
              f"cells={n_cells} tree_stemc mean={np.nanmean(tm):.0f} max={np.nanmax(tm):.0f} gC/m2 "
              f"peak RSS {rss_gb:.1f} GB", flush=True)

    # Output is a compressed .npz. The earlier netCDF writes failed with
    # "NetCDF: HDF error" (jobs 596645, 596680) because the scratch project
    # quota was exceeded (EDQUOT, shown plainly by job 596686), not because
    # of netCDF itself; .npz is kept as a simple, adequate format.
    assert out_nc.endswith(".npz"), "output path must end in .npz"
    arrays = {key: np.stack(maps[key]).astype("f4") for key in maps}
    meta = {
        "units": ("tree_stemc, shrub_stemc: gC/m^2 per gridcell land area; stemc_dens_by_type: gC/m^2 per unit "
                  "area of that PFT type; tree_frac, veg_frac, frac_by_type: 1; area: km^2"),
        "definition": ("tree_stemc = sum over tree PFTs (itype 1-8) of (LIVESTEMC+DEADSTEMC) x pfts1d_wtgcell; "
                       "shrub_stemc likewise for itype 9-11; tree_frac/veg_frac = summed wtgcell; "
                       "*_by_type have dims (year, tree_type, lat, lon) with tree_type = itype 1..8, and "
                       "tree_stemc = sum_t stemc_dens_by_type * frac_by_type"),
        "note": ("Annual values are day-weighted means of monthly h1 records; pfts1d_wtgcell is the value "
                 "stored in each year's h1 file. Intended to match the ESA CCI AGB definition (woody parts "
                 "of trees, per unit area). ELM has no separate stump pool; coarse roots are separate "
                 "pools and are excluded. Values are carbon, not dry biomass."),
        "case": case, "run_dir": run_dir,
    }
    tmp = out_nc + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), tree_type=np.array(TREE_TYPES, "i4"),
                            lat=lat, lon=lon, landfrac=landfrac, area=area,
                            **arrays, **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_nc)
    print(f"wrote {out_nc} ({os.path.getsize(out_nc) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
