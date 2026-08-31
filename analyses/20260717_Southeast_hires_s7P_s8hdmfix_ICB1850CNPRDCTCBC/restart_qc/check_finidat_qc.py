#!/usr/bin/env python3
"""QC checks for a Southeast ELM restart finidat and matching h0 file.

The restart file is large and stores internal state variables without complete
history-style metadata. This script therefore checks restart pool consistency
directly, and uses the matching h0 file for interpretable GPP/NPP and
area-weighted gridcell diagnostics.
"""

from __future__ import annotations

import json
import math
import os
from collections import Counter
from datetime import datetime, timezone

import numpy as np
from netCDF4 import Dataset


CASE = "20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC"
RUN_DIR = f"/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/{CASE}/run"
RESTART_PATH = os.path.join(RUN_DIR, f"{CASE}.elm.r.0441-01-01-00000.nc")
H0_PATH = os.path.join(RUN_DIR, f"{CASE}.elm.h0.0441-01-01-00000.nc")
OUT_JSON = os.path.join(RUN_DIR, "finidat_0441_qc_summary.json")
OUT_TXT = os.path.join(RUN_DIR, "finidat_0441_qc_summary.txt")

SECONDS_PER_NOLEAP_YEAR = 365 * 24 * 60 * 60

PFT_C_POOLS = [
    "leafc",
    "frootc",
    "livestemc",
    "deadstemc",
    "livecrootc",
    "deadcrootc",
]

PFT_C_POOL_TERMS_FOR_TOTVEGC = [
    f"{base}{suffix}"
    for base in PFT_C_POOLS
    for suffix in ("", "_storage", "_xfer")
]

PFT_CHECK_VARS = [
    "tlai",
    "leafc",
    "frootc",
    "livestemc",
    "deadstemc",
    "livecrootc",
    "deadcrootc",
    "totvegc",
    "tempsum_npp",
    "annsum_npp",
    "tempsum_potential_gpp",
    "annsum_potential_gpp",
    "gpp_pepv",
]

COLUMN_CHECK_VARS = [
    "totsomc",
    "cwdc_vr",
    "soil1c_vr",
    "soil2c_vr",
    "soil3c_vr",
    "soil4c_vr",
]

H0_CHECK_VARS = [
    "GPP",
    "NPP",
    "AR",
    "HR",
    "ER",
    "NEE",
    "TOTVEGC",
    "TOTSOMC",
    "TOTSOMC_1m",
    "TOTLITC",
    "CWDC",
    "LEAFC",
    "FROOTC",
    "LIVESTEMC",
    "DEADSTEMC",
    "LIVECROOTC",
    "DEADCROOTC",
    "TLAI",
    "ZWT",
    "BTRAN",
]

PFT_TYPE_NAMES = {
    0: "not_vegetated",
    1: "needleleaf_evergreen_temperate_tree",
    2: "needleleaf_evergreen_boreal_tree",
    3: "needleleaf_deciduous_boreal_tree",
    4: "broadleaf_evergreen_tropical_tree",
    5: "broadleaf_evergreen_temperate_tree",
    6: "broadleaf_deciduous_tropical_tree",
    7: "broadleaf_deciduous_temperate_tree",
    8: "broadleaf_deciduous_boreal_tree",
    9: "broadleaf_evergreen_shrub",
    10: "broadleaf_deciduous_temperate_shrub",
    11: "broadleaf_deciduous_boreal_shrub",
    12: "c3_arctic_grass",
    13: "c3_non_arctic_grass",
    14: "c4_grass",
    15: "c3_crop",
    16: "c3_irrigated",
}


def read_ma(ds: Dataset, name: str) -> np.ma.MaskedArray:
    var = ds.variables[name]
    arr = np.ma.array(var[:])
    fill = getattr(var, "_FillValue", None)
    missing = getattr(var, "missing_value", None)
    if fill is not None:
        arr = np.ma.masked_where(arr == fill, arr)
    if missing is not None:
        arr = np.ma.masked_where(arr == missing, arr)
    arr = np.ma.masked_invalid(arr)
    return arr


def as_float_values(arr: np.ma.MaskedArray, mask: np.ndarray | None = None) -> np.ndarray:
    if mask is not None:
        arr = np.ma.array(arr, mask=np.ma.getmaskarray(arr) | ~mask)
    vals = arr.compressed().astype(np.float64, copy=False)
    return vals[np.isfinite(vals)]


def summarize_values(vals: np.ndarray) -> dict[str, float | int | None]:
    if vals.size == 0:
        return {
            "count": 0,
            "min": None,
            "p01": None,
            "p05": None,
            "median": None,
            "mean": None,
            "p95": None,
            "p99": None,
            "max": None,
            "negative_count": 0,
            "zero_count": 0,
        }
    quant = np.quantile(vals, [0.01, 0.05, 0.5, 0.95, 0.99])
    return {
        "count": int(vals.size),
        "min": float(np.min(vals)),
        "p01": float(quant[0]),
        "p05": float(quant[1]),
        "median": float(quant[2]),
        "mean": float(np.mean(vals)),
        "p95": float(quant[3]),
        "p99": float(quant[4]),
        "max": float(np.max(vals)),
        "negative_count": int(np.sum(vals < 0.0)),
        "zero_count": int(np.sum(vals == 0.0)),
    }


def weighted_mean(vals: np.ndarray, weights: np.ndarray) -> float | None:
    good = np.isfinite(vals) & np.isfinite(weights) & (weights > 0.0)
    if not np.any(good):
        return None
    return float(np.sum(vals[good] * weights[good]) / np.sum(weights[good]))


def summarize_masked(arr: np.ma.MaskedArray, mask: np.ndarray | None = None) -> dict:
    vals = as_float_values(arr, mask)
    out = summarize_values(vals)
    out["masked_or_nonfinite_count"] = int(arr.size - vals.size if mask is None else np.sum(mask) - vals.size)
    return out


def h0_var_stats(ds: Dataset, name: str, land_weights: np.ndarray, land_mask: np.ndarray) -> dict:
    arr = read_ma(ds, name)
    if arr.ndim == 3:
        arr2 = arr[0, :, :]
    else:
        arr2 = arr
    vals = as_float_values(arr2, land_mask)
    stat = summarize_values(vals)
    dense = np.asarray(np.ma.filled(arr2, np.nan), dtype=np.float64)
    stat["area_weighted_mean_native_units"] = weighted_mean(dense, land_weights)
    stat["units"] = getattr(ds.variables[name], "units", "")
    stat["long_name"] = getattr(ds.variables[name], "long_name", "")
    if stat["units"] == "gC/m^2/s":
        annual = dense * SECONDS_PER_NOLEAP_YEAR
        annual_vals = annual[land_mask & np.isfinite(annual)]
        annual_stat = summarize_values(annual_vals)
        annual_stat["area_weighted_mean_gC_m2_yr"] = weighted_mean(annual, land_weights)
        stat["annualized_gC_m2_yr"] = annual_stat
    elif stat["units"] == "gC/m^2":
        kg = dense / 1000.0
        kg_vals = kg[land_mask & np.isfinite(kg)]
        kg_stat = summarize_values(kg_vals)
        kg_stat["area_weighted_mean_kgC_m2"] = weighted_mean(kg, land_weights)
        stat["kgC_m2"] = kg_stat
    return stat


def ratio_stats(numerator: np.ndarray, denominator: np.ndarray, land_mask: np.ndarray) -> dict:
    good = land_mask & np.isfinite(numerator) & np.isfinite(denominator) & (denominator > 1.0e-12)
    ratio = numerator[good] / denominator[good]
    return summarize_values(ratio)


def main() -> None:
    report: dict = {
        "case": CASE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "restart_path": RESTART_PATH,
        "h0_path": H0_PATH,
        "notes": [
            "Restart variables mostly have blank unit attributes; interpret ranges using matching h0 units where possible.",
            "h0 variables are not pre-weighted by land fraction; area-weighted means use area * landfrac over landmask==1.",
        ],
    }

    with Dataset(RESTART_PATH) as rst:
        report["restart_dimensions"] = {name: len(dim) for name, dim in rst.dimensions.items()}
        report["restart_global_attrs"] = {
            key: str(getattr(rst, key))
            for key in ["history", "case_id", "surface_dataset", "source", "version"]
            if hasattr(rst, key)
        }
        report["restart_dates"] = {
            key: int(np.asarray(rst.variables[key][:]).item())
            for key in [
                "timemgr_rst_start_ymd",
                "timemgr_rst_ref_ymd",
                "timemgr_rst_curr_ymd",
                "timemgr_rst_curr_tod",
            ]
            if key in rst.variables
        }

        grid_lon = as_float_values(read_ma(rst, "grid1d_lon"))
        grid_lat = as_float_values(read_ma(rst, "grid1d_lat"))
        report["restart_domain"] = {
            "lon_min": float(np.min(grid_lon)),
            "lon_max": float(np.max(grid_lon)),
            "lat_min": float(np.min(grid_lat)),
            "lat_max": float(np.max(grid_lat)),
        }

        pft_active = np.asarray(read_ma(rst, "pfts1d_active").filled(0), dtype=np.int16) == 1
        pft_type = np.asarray(read_ma(rst, "pfts1d_itypveg").filled(-9999), dtype=np.int16)
        pft_wtxy = np.asarray(read_ma(rst, "pfts1d_wtxy").filled(np.nan), dtype=np.float64)
        col_active = np.asarray(read_ma(rst, "cols1d_active").filled(0), dtype=np.int16) == 1
        land_active = np.asarray(read_ma(rst, "land1d_active").filled(0), dtype=np.int16) == 1

        type_counts = Counter(map(int, pft_type[pft_active]))
        type_weight_sums = {
            f"{ityp}:{PFT_TYPE_NAMES.get(ityp, 'unknown')}": float(np.nansum(pft_wtxy[pft_active & (pft_type == ityp)]))
            for ityp in sorted(type_counts)
        }
        report["restart_active_counts"] = {
            "landunit_active": int(np.sum(land_active)),
            "column_active": int(np.sum(col_active)),
            "pft_active": int(np.sum(pft_active)),
            "pft_type_counts": {
                f"{ityp}:{PFT_TYPE_NAMES.get(ityp, 'unknown')}": int(count)
                for ityp, count in sorted(type_counts.items())
            },
            "pft_wtxy_sum_by_type": type_weight_sums,
        }

        report["restart_pft_stats"] = {}
        pft_arrays = {}
        for name in PFT_CHECK_VARS:
            if name not in rst.variables:
                continue
            arr = read_ma(rst, name)
            pft_arrays[name] = np.asarray(np.ma.filled(arr, np.nan), dtype=np.float64)
            stat = summarize_masked(arr, pft_active)
            stat["wtxy_weighted_mean"] = weighted_mean(pft_arrays[name], np.where(pft_active, pft_wtxy, np.nan))
            report["restart_pft_stats"][name] = stat

        report["restart_totvegc_consistency"] = {}
        if all(name in pft_arrays for name in PFT_C_POOLS + ["totvegc"]):
            veg_current = np.zeros_like(pft_arrays["totvegc"], dtype=np.float64)
            for name in PFT_C_POOLS:
                veg_current += pft_arrays[name]
            diff = pft_arrays["totvegc"] - veg_current
            good = pft_active & np.isfinite(diff)
            abs_diff = np.abs(diff[good])
            report["restart_totvegc_consistency"]["current_pools_only"] = {
                "formula": "totvegc - (leafc + frootc + livestemc + deadstemc + livecrootc + deadcrootc)",
                "count": int(abs_diff.size),
                "mean_abs_diff": float(np.mean(abs_diff)) if abs_diff.size else None,
                "p99_abs_diff": float(np.quantile(abs_diff, 0.99)) if abs_diff.size else None,
                "max_abs_diff": float(np.max(abs_diff)) if abs_diff.size else None,
                "nonzero_gt_1e-8_count": int(np.sum(abs_diff > 1.0e-8)) if abs_diff.size else 0,
            }

        if "totvegc" in pft_arrays and all(name in rst.variables for name in PFT_C_POOL_TERMS_FOR_TOTVEGC):
            veg_all = np.zeros_like(pft_arrays["totvegc"], dtype=np.float64)
            for name in PFT_C_POOL_TERMS_FOR_TOTVEGC:
                if name in pft_arrays:
                    vals = pft_arrays[name]
                else:
                    vals = np.asarray(np.ma.filled(read_ma(rst, name), np.nan), dtype=np.float64)
                veg_all += vals
            diff = pft_arrays["totvegc"] - veg_all
            good = pft_active & np.isfinite(diff)
            abs_diff = np.abs(diff[good])
            report["restart_totvegc_consistency"]["current_storage_xfer_pools"] = {
                "formula": "totvegc - sum((leaf/froot/livestem/deadstem/livecroot/deadcroot)c with '', _storage, _xfer suffixes)",
                "count": int(abs_diff.size),
                "mean_abs_diff": float(np.mean(abs_diff)) if abs_diff.size else None,
                "p99_abs_diff": float(np.quantile(abs_diff, 0.99)) if abs_diff.size else None,
                "max_abs_diff": float(np.max(abs_diff)) if abs_diff.size else None,
                "nonzero_gt_1e-8_count": int(np.sum(abs_diff > 1.0e-8)) if abs_diff.size else 0,
            }

        report["restart_column_stats"] = {}
        for name in COLUMN_CHECK_VARS:
            if name not in rst.variables:
                continue
            arr = read_ma(rst, name)
            if arr.ndim == 1:
                mask = col_active
            elif arr.ndim == 2 and arr.shape[0] == col_active.shape[0]:
                mask = np.broadcast_to(col_active[:, None], arr.shape)
            elif arr.ndim == 2 and arr.shape[1] == col_active.shape[0]:
                mask = np.broadcast_to(col_active[None, :], arr.shape)
            else:
                mask = None
            report["restart_column_stats"][name] = summarize_masked(arr, mask)

    with Dataset(H0_PATH) as h0:
        report["h0_dimensions"] = {name: len(dim) for name, dim in h0.dimensions.items()}
        report["h0_time"] = {
            "time_days_since_0001": float(np.asarray(h0.variables["time"][:]).item()),
            "mcdate": int(np.asarray(h0.variables["mcdate"][:]).item()),
            "mcsec": int(np.asarray(h0.variables["mcsec"][:]).item()),
            "time_bounds_days_since_0001": [float(x) for x in np.asarray(h0.variables["time_bounds"][0, :])],
            "covered_years_noleap": float((h0.variables["time_bounds"][0, 1] - h0.variables["time_bounds"][0, 0]) / 365.0),
        }

        area = np.asarray(read_ma(h0, "area").filled(np.nan), dtype=np.float64)
        landfrac = np.asarray(read_ma(h0, "landfrac").filled(np.nan), dtype=np.float64)
        landmask_raw = np.asarray(read_ma(h0, "landmask").filled(0), dtype=np.int16)
        land_mask = (landmask_raw == 1) & np.isfinite(area) & np.isfinite(landfrac) & (area > 0) & (landfrac > 0)
        land_weights = np.where(land_mask, area * landfrac, np.nan)
        report["h0_land_area"] = {
            "land_cells": int(np.sum(land_mask)),
            "total_land_area_km2": float(np.nansum(land_weights)),
            "landfrac_min": float(np.nanmin(landfrac[land_mask])),
            "landfrac_max": float(np.nanmax(landfrac[land_mask])),
        }

        report["h0_stats"] = {}
        for name in H0_CHECK_VARS:
            if name in h0.variables:
                report["h0_stats"][name] = h0_var_stats(h0, name, land_weights, land_mask)

        if "GPP" in h0.variables and "NPP" in h0.variables:
            gpp = np.asarray(np.ma.filled(read_ma(h0, "GPP")[0, :, :], np.nan), dtype=np.float64)
            npp = np.asarray(np.ma.filled(read_ma(h0, "NPP")[0, :, :], np.nan), dtype=np.float64)
            report["h0_npp_gpp_ratio"] = ratio_stats(npp, gpp, land_mask)
            report["h0_npp_greater_than_gpp_cells"] = int(np.sum(land_mask & np.isfinite(gpp) & np.isfinite(npp) & (npp > gpp)))

        agb_components = ["LEAFC", "LIVESTEMC", "DEADSTEMC"]
        if all(name in h0.variables for name in agb_components):
            agb = np.zeros_like(area, dtype=np.float64)
            for name in agb_components:
                agb += np.asarray(np.ma.filled(read_ma(h0, name)[0, :, :], np.nan), dtype=np.float64)
            agb_kg = agb / 1000.0
            vals = agb_kg[land_mask & np.isfinite(agb_kg)]
            report["h0_aboveground_biomass_kgC_m2"] = summarize_values(vals)
            report["h0_aboveground_biomass_kgC_m2"]["area_weighted_mean_kgC_m2"] = weighted_mean(agb_kg, land_weights)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(f"QC report for {CASE}\n")
        f.write(f"Restart: {RESTART_PATH}\n")
        f.write(f"h0:      {H0_PATH}\n\n")
        f.write(json.dumps(report, indent=2, sort_keys=True))
        f.write("\n")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_TXT}")


if __name__ == "__main__":
    main()
