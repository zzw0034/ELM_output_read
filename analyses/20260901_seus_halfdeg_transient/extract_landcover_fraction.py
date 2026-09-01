"""
Domain-mean annual land-cover fraction time series for
20260901_seus_halfdeg_transient, to check whether the TOTVEGC_ABG dip
(bottoming out in 1957, see extract_annual_timeseries.py) is actually a
forest-area effect (LUH2-driven forest -> cropland -> forest transition)
rather than something else.

Uses PCT_NAT_PFT (% of each natpft within the natural-vegetation landunit)
and PCT_LANDUNIT (% of each landunit type on the gridcell). Verified against
this run's own paramfile (clm_params.nc's source, ELM's pftvarcon.F90
expected_pftnames list) that natpft indices are the standard ELM/CLM
ordering: 0=bare, 1-8=trees, 9-11=shrubs, 12-14=grass, 15-16=generic crop
(rainfed/irrigated, unmanaged -- this run has no separate managed-crop
landunit; PCT_LANDUNIT's crop entry (ltype=2) is 0 everywhere sampled).

Forest/shrub/grass/crop/bare fractions are expressed as % of gridcell land
area: group_pct_of_gridcell = PCT_LANDUNIT[veg]/100 * sum(PCT_NAT_PFT[group]).

Runs on Pathfinder. Domain is tiny (27x42), so this runs directly without
Slurm, same as extract_spatial_maps.py.

Usage: python extract_landcover_fraction.py
"""

import os
import sys

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import aggregate_monthly_to_yearly

CASE = "20260901_seus_halfdeg_transient"
RUN_DIR = f"/scratch/hpcl-cli185/zw5/cime_output_dirs/{CASE}/run"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

# 0-based natpft index groups (see module docstring)
TREE_IDX = slice(1, 9)
SHRUB_IDX = slice(9, 12)
GRASS_IDX = slice(12, 15)
CROP_IDX = slice(15, 17)
BARE_IDX = slice(0, 1)

LTYPE_VEG = 0   # ltype=1 (1-based) -> index 0
LTYPE_CROP = 1  # ltype=2 (1-based) -> index 1

VARS = ["PCT_NAT_PFT", "PCT_LANDUNIT"]
COORD_VARS = ["area", "landfrac"]


def load_all_vars(files: list[str]) -> xr.Dataset:
    per_var = {v: [] for v in VARS}
    static = {}
    got_static = False
    for f in files:
        with xr.open_dataset(f, decode_times=True) as ds:
            if ds.sizes.get("time", 0) < 12:
                print(f"  skipping {os.path.basename(f)} (time size {ds.sizes.get('time')}, not a monthly bundle)")
                continue
            for v in VARS:
                per_var[v].append(ds[v].load())
            if not got_static:
                for c in COORD_VARS:
                    static[c] = ds[c].load()
                got_static = True
    out = xr.Dataset({v: xr.concat(das, dim="time") for v, das in per_var.items()})
    for c, da in static.items():
        out[c] = da
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    files = find_h0_files(RUN_DIR)
    print(f"Found {len(files)} h0 files")

    ds = load_all_vars(files)
    weight = (ds["area"] * ds["landfrac"]).fillna(0.0)

    def weighted_annual(da_yearly: xr.DataArray) -> xr.DataArray:
        return da_yearly.weighted(weight).mean(dim=["lat", "lon"], skipna=True)

    veg_lu_pct = ds["PCT_LANDUNIT"].isel(ltype=LTYPE_VEG)     # (time, lat, lon), %
    crop_lu_pct = ds["PCT_LANDUNIT"].isel(ltype=LTYPE_CROP)   # (time, lat, lon), %

    groups = {
        "forest_frac": TREE_IDX,
        "shrub_frac": SHRUB_IDX,
        "grass_frac": GRASS_IDX,
        "crop_as_pft_frac": CROP_IDX,
        "bare_frac": BARE_IDX,
    }

    result = {}
    for name, idx in groups.items():
        pct_of_veg_lu = ds["PCT_NAT_PFT"].isel(natpft=idx).sum(dim="natpft")  # % of veg landunit
        pct_of_gridcell = veg_lu_pct / 100.0 * pct_of_veg_lu                  # % of gridcell
        yearly = aggregate_monthly_to_yearly(pct_of_gridcell, method="mean")
        result[name] = weighted_annual(yearly)

    crop_lu_yearly = aggregate_monthly_to_yearly(crop_lu_pct, method="mean")
    result["crop_landunit_frac"] = weighted_annual(crop_lu_yearly)
    result["crop_total_frac"] = result["crop_as_pft_frac"] + result["crop_landunit_frac"]

    out = xr.Dataset(result)
    for v in out.data_vars:
        out[v].attrs = {"units": "% of gridcell land area", "long_name": v}
    out.attrs["case"] = CASE
    out.attrs["weighting"] = "area*landfrac, weighted spatial mean over lat/lon"

    for v in out.data_vars:
        vals = out[v].values
        print(f"  {v:20s} first={vals[0]:.3f}  last={vals[-1]:.3f}  "
              f"min={np.nanmin(vals):.3f}  max={np.nanmax(vals):.3f}  "
              f"min_year={int(out['year'].values[np.nanargmin(vals)])}")

    out_path = os.path.join(OUT_DIR, "landcover_fraction.nc")
    out.to_netcdf(out_path)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
