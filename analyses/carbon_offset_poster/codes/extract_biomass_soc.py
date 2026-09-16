"""
Extract ELM aboveground biomass (TOTVEGC_ABG) and soil organic carbon
integrated to 0-30 cm from a transient/historical ELM run, for the poster's
"0.5 deg vs 4 km vs observations" biomass/SOC comparison panel.

0-30 cm (not the 0-100 cm used by
../../20260723_..._harvfix/extract_biomass_soc.py), to match SoilGrids'
native 0-5/5-15/15-30 cm depth layers and HWSD's topsoil ("S") layer
directly, per paper_carbon_offset/RESULTS_SUMMARY.md's caution against
comparing a full-column model SOC to a shallower observational product
("土壤深度口径要统一,不能全土柱对0-30cm").

Depth integration: SOIL1C_vr..SOIL4C_vr are ELM's vertically-resolved SOM
pools (gC/m^3) on the `levdcmp` grid. DZSOI (layer thickness, m) is read
from the run's own h0 file -- confirmed spatially uniform over land for
both the 4 km and 0.5 deg SEUS cases (same 15-layer column everywhere,
levgrnd == levdcmp) -- so one representative land column's cumulative
depths set each layer's overlap (in metres) with [0, 0.30 m], and
    SOC_0_30 = sum_k overlap_k * (SOIL1C_vr+SOIL2C_vr+SOIL3C_vr+SOIL4C_vr)_k
in gC/m^3 * m = gC/m^2. This is derived from the file at runtime, not
hardcoded, in case a future case's soil grid differs.

Runs on Pathfinder via Slurm (see submit_py.sbatch); do not run on a login
node (AGENTS.md). One year's h0 file is loaded, reduced to two 2-D
annual-mean maps, and discarded before the next year, so peak memory stays
at O(1 year) even for the 324x504 4 km grid.

Usage:
    python extract_biomass_soc.py --case <name> --run-dir <path> --tag <4km|0.5deg> \
        --out-dir <path> [--year-min 2014] [--year-max 2020]
"""
import argparse
import os
import sys

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
from elmtools.io import find_h0_files
from elmtools.process import subtract_month_cftime

SOC_POOLS = ["SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]
TARGET_DEPTH_M = 0.30


def layer_weights_0_30cm(dzsoi_da: xr.DataArray, expected_nlev: int) -> np.ndarray:
    """Return a 1-D array (m), one entry per decomposition layer: the
    portion of that layer's thickness that falls within [0, 0.30 m].
    Derived from one valid (non-NaN) land column of *dzsoi_da*
    (dims (levgrnd|levdcmp, lat, lon)); confirmed spatially uniform for
    both cases this script targets, so any valid column gives the same
    answer."""
    levdim = dzsoi_da.dims[0]
    nlev = dzsoi_da.sizes[levdim]
    assert nlev == expected_nlev, (
        f"DZSOI has {nlev} levels on '{levdim}' but SOIL*_vr has {expected_nlev} "
        "levels -- can't assume they share a grid; inspect this case by hand."
    )
    flat = dzsoi_da.values.reshape(nlev, -1)
    valid_cols = ~np.isnan(flat).any(axis=0)
    if not valid_cols.any():
        raise ValueError("No valid (non-NaN) DZSOI column found in this file")
    profile = flat[:, np.where(valid_cols)[0][0]]
    z_bottom = np.cumsum(profile)
    z_top = z_bottom - profile
    overlap = np.clip(np.minimum(z_bottom, TARGET_DEPTH_M) - z_top, 0.0, None)
    return overlap


def soc_0_30_annual_mean(ds: xr.Dataset, weights: np.ndarray, levdim: str) -> xr.DataArray:
    """ds has dims (time=12, levdim, lat, lon) for the SOC_POOLS vars,
    already restricted to one calendar year. Returns a (lat, lon) map:
    the year's mean of the depth-integrated 0-30 cm stock (gC/m^2)."""
    total_vr = sum(ds[v] for v in SOC_POOLS)  # gC/m^3, dims (time, levdim, lat, lon)
    w = xr.DataArray(weights, dims=[levdim])
    stock = (total_vr * w).sum(dim=levdim)  # gC/m^2, dims (time, lat, lon)
    return stock.mean(dim="time", skipna=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--tag", required=True, help="short label used in the output filename, e.g. 4km or 0.5deg")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--year-min", type=int, default=2014)
    ap.add_argument("--year-max", type=int, default=2020)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    files = find_h0_files(args.run_dir, year_min=args.year_min, year_max=args.year_max)
    n_expected = args.year_max - args.year_min + 1
    print(f"[{args.tag}] Found {len(files)} h0 files for {args.year_min}-{args.year_max} "
          f"(expected {n_expected})")
    assert len(files) == n_expected, "expected exactly one h0 file per year"

    need_vars = ["TOTVEGC_ABG", "DZSOI"] + SOC_POOLS
    weights = None
    levdim = None
    lat = lon = None
    biomass_years = []
    soc_years = []

    for f in files:
        print(f"  reading {os.path.basename(f)}")
        with xr.open_dataset(f) as ds_raw:
            ds = ds_raw[need_vars].load()

        # h0 monthly records are stamped on the 1st of the *following*
        # month; relabel to the true month before taking a calendar-year
        # mean (same convention as extract_biomass_soc.py in the sibling
        # harvfix folder).
        corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
        ds = ds.assign_coords(time=corrected)

        if weights is None:
            levdim = ds["SOIL1C_vr"].dims[1]
            expected_nlev = ds["SOIL1C_vr"].sizes[levdim]
            weights = layer_weights_0_30cm(ds["DZSOI"], expected_nlev)
            lat = ds["lat"].values
            lon = ds["lon"].values
            print(f"  [{args.tag}] 0-30cm layer weights (m): {np.round(weights, 4).tolist()}  "
                  f"sum={weights.sum():.4f} (should be 0.30)")

        biomass_years.append(ds["TOTVEGC_ABG"].mean(dim="time", skipna=True))
        soc_years.append(soc_0_30_annual_mean(ds, weights, levdim))

    biomass_mean = xr.concat(biomass_years, dim="year").mean(dim="year", skipna=True) / 1000.0  # kgC/m^2
    soc_mean = xr.concat(soc_years, dim="year").mean(dim="year", skipna=True) / 1000.0  # kgC/m^2

    print(f"  [{args.tag}] TOTVEGC_ABG {args.year_min}-{args.year_max} mean [kgC/m^2]  "
          f"min={float(biomass_mean.min()):.3f} max={float(biomass_mean.max()):.3f} "
          f"mean={float(biomass_mean.mean()):.3f}")
    print(f"  [{args.tag}] SOC_0_30cm  {args.year_min}-{args.year_max} mean [kgC/m^2]  "
          f"min={float(soc_mean.min()):.3f} max={float(soc_mean.max()):.3f} "
          f"mean={float(soc_mean.mean()):.3f}")

    out = xr.Dataset(
        {
            "TOTVEGC_ABG_mean": (("lat", "lon"), biomass_mean.values.astype("float32")),
            "SOC_0_30cm_mean": (("lat", "lon"), soc_mean.values.astype("float32")),
        },
        coords={"lat": lat, "lon": lon},
    )
    out["TOTVEGC_ABG_mean"].attrs = {
        "units": "kgC/m^2",
        "long_name": f"TOTVEGC_ABG (aboveground biomass), {args.year_min}-{args.year_max} mean of annual means",
    }
    out["SOC_0_30cm_mean"].attrs = {
        "units": "kgC/m^2",
        "long_name": f"SOC 0-30cm (SOIL1-4C_vr depth-integrated), {args.year_min}-{args.year_max} mean",
    }
    out.attrs["case"] = args.case
    out.attrs["run_dir"] = args.run_dir

    out_path = os.path.join(args.out_dir, f"ELM_biomass_soc_0_30cm_{args.tag}.nc")
    out.to_netcdf(out_path)
    print(f"\n[{args.tag}] Wrote {out_path}")


if __name__ == "__main__":
    main()
