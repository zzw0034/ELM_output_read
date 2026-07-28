#!/usr/bin/env python
"""Diagnose low GPP in the southeastern part of the Southeast ELM domain."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np
import xarray as xr


NC_PATH = Path(os.environ["NC_PATH"])
SURFDATA_PATH = Path(os.environ["SURFDATA_PATH"])
OUT_DIR = Path(os.environ["OUT_DIR"])
SECONDS_PER_YEAR = 365.0 * 86400.0
FILL_LIMIT = 1.0e30

DRIVERS = ("TLAI", "BTRAN", "FPG", "FPG_P", "FSDS", "TBOT", "TOTVEGC")
OUTPUT_NAMES = (
    "GPP_gC_m2_yr",
    "TLAI",
    "BTRAN",
    "FPG",
    "FPG_P",
    "FSDS_W_m2",
    "TBOT_C",
    "TOTVEGC_gC_m2",
)

PFT_NAMES = (
    "not_vegetated",
    "needleleaf_evergreen_temperate_tree",
    "needleleaf_evergreen_boreal_tree",
    "needleleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_tropical_tree",
    "broadleaf_evergreen_temperate_tree",
    "broadleaf_deciduous_tropical_tree",
    "broadleaf_deciduous_temperate_tree",
    "broadleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_shrub",
    "broadleaf_deciduous_temperate_shrub",
    "broadleaf_deciduous_boreal_shrub",
    "c3_arctic_grass",
    "c3_non_arctic_grass",
    "c4_grass",
    "crop",
    "irrigated_crop",
)


def clean(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    result[~np.isfinite(result) | (np.abs(result) >= FILL_LIMIT)] = np.nan
    return result


def weighted_mean(values: np.ndarray, weights: np.ndarray, mask: np.ndarray) -> float:
    valid = mask & np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(valid):
        return float("nan")
    return float(np.average(values[valid], weights=weights[valid]))


def summarize_group(
    group: str,
    mask: np.ndarray,
    weights: np.ndarray,
    arrays: dict[str, np.ndarray],
) -> dict[str, float | int | str]:
    row: dict[str, float | int | str] = {
        "group": group,
        "n_cells": int(np.count_nonzero(mask)),
        "weight_sum": float(np.nansum(np.where(mask, weights, np.nan))),
    }
    for name in OUTPUT_NAMES:
        row[name] = weighted_mean(arrays[name], weights, mask)
    gpp = arrays["GPP_gC_m2_yr"]
    row["GPP_median_gC_m2_yr"] = float(np.nanmedian(np.where(mask, gpp, np.nan)))
    row["near_zero_GPP_share"] = float(
        np.count_nonzero(mask & np.isfinite(gpp) & (gpp < 1.0))
        / max(np.count_nonzero(mask & np.isfinite(gpp)), 1)
    )
    return row


def correlation_rows(
    scope: str,
    mask: np.ndarray,
    arrays: dict[str, np.ndarray],
) -> list[dict[str, float | int | str]]:
    rows = []
    gpp = arrays["GPP_gC_m2_yr"]
    for name in OUTPUT_NAMES[1:]:
        driver = arrays[name]
        valid = mask & np.isfinite(gpp) & np.isfinite(driver)
        if np.count_nonzero(valid) < 3:
            corr = float("nan")
        else:
            corr = float(np.corrcoef(gpp[valid], driver[valid])[0, 1])
        rows.append(
            {
                "scope": scope,
                "driver": name,
                "pearson_r_with_GPP": corr,
                "n_cells": int(np.count_nonzero(valid)),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(NC_PATH, decode_times=False)

    required = {"GPP", "lat", "lon", "area", "landfrac", "landmask", *DRIVERS}
    missing = sorted(required.difference(ds.variables))
    if missing:
        raise KeyError(f"Missing required variables: {missing}")

    lat = clean(ds["lat"].values)
    lon = clean(ds["lon"].values)
    lon2d, lat2d = np.meshgrid(lon, lat)
    area = clean(ds["area"].values)
    landfrac = clean(ds["landfrac"].values)
    landmask_values = np.asarray(ds["landmask"].values)
    weights = area * landfrac

    raw_gpp = clean(ds["GPP"].isel(time=0).values)
    arrays = {
        "GPP_gC_m2_yr": raw_gpp * SECONDS_PER_YEAR,
        "TLAI": clean(ds["TLAI"].isel(time=0).values),
        "BTRAN": clean(ds["BTRAN"].isel(time=0).values),
        "FPG": clean(ds["FPG"].isel(time=0).values),
        "FPG_P": clean(ds["FPG_P"].isel(time=0).values),
        "FSDS_W_m2": clean(ds["FSDS"].isel(time=0).values),
        "TBOT_C": clean(ds["TBOT"].isel(time=0).values) - 273.15,
        "TOTVEGC_gC_m2": clean(ds["TOTVEGC"].isel(time=0).values),
    }

    land = (
        (landmask_values == 1)
        & np.isfinite(landfrac)
        & (landfrac >= 0.5)
        & np.isfinite(arrays["GPP_gC_m2_yr"])
    )
    vegetated = land & np.isfinite(arrays["TLAI"]) & (arrays["TLAI"] > 0.1)

    # Bounding box chosen from the visible low-GPP pattern: Florida, southern
    # Georgia/Alabama, and the adjacent coastal plain.
    southeast = (lon2d >= -85.5) & (lat2d <= 32.5)
    southeast_land = land & southeast
    other_land = land & ~southeast
    southeast_vegetated = vegetated & southeast
    other_vegetated = vegetated & ~southeast

    florida = (lon2d >= -83.5) & (lat2d <= 30.5)
    adjacent_north = (lon2d >= -85.5) & (lat2d > 30.5) & (lat2d <= 33.5)
    adjacent_west = (
        (lon2d >= -88.0)
        & (lon2d < -83.5)
        & (lat2d <= 30.5)
    )

    regional_rows = [
        summarize_group("southeast_all_land", southeast_land, weights, arrays),
        summarize_group("other_all_land", other_land, weights, arrays),
        summarize_group("southeast_vegetated", southeast_vegetated, weights, arrays),
        summarize_group("other_vegetated", other_vegetated, weights, arrays),
        summarize_group("florida_all_land", land & florida, weights, arrays),
        summarize_group("florida_vegetated", vegetated & florida, weights, arrays),
        summarize_group("adjacent_north_all_land", land & adjacent_north, weights, arrays),
        summarize_group("adjacent_west_all_land", land & adjacent_west, weights, arrays),
    ]
    write_csv(OUT_DIR / "regional_summary.csv", regional_rows)

    gpp_valid = arrays["GPP_gC_m2_yr"][vegetated]
    q20, q80 = np.nanquantile(gpp_valid, [0.2, 0.8])
    low20 = vegetated & (arrays["GPP_gC_m2_yr"] <= q20)
    middle60 = vegetated & (arrays["GPP_gC_m2_yr"] > q20) & (
        arrays["GPP_gC_m2_yr"] < q80
    )
    high20 = vegetated & (arrays["GPP_gC_m2_yr"] >= q80)
    quantile_rows = [
        summarize_group("lowest_20pct_GPP", low20, weights, arrays),
        summarize_group("middle_60pct_GPP", middle60, weights, arrays),
        summarize_group("highest_20pct_GPP", high20, weights, arrays),
    ]
    write_csv(OUT_DIR / "gpp_quantile_summary.csv", quantile_rows)

    correlations = correlation_rows("all_vegetated_land", vegetated, arrays)
    correlations.extend(
        correlation_rows("southeast_vegetated", southeast_vegetated, arrays)
    )
    write_csv(OUT_DIR / "driver_correlations.csv", correlations)

    surf = xr.open_dataset(SURFDATA_PATH, decode_times=False)
    surface_required = {
        "PCT_NAT_PFT",
        "PCT_NATVEG",
        "PCT_CROP",
        "PCT_URBAN",
        "PCT_LAKE",
        "PCT_WETLAND",
        "PCT_GLACIER",
    }
    surface_missing = sorted(surface_required.difference(surf.variables))
    if surface_missing:
        raise KeyError(f"Missing required surface variables: {surface_missing}")

    landcover_arrays = {
        "PCT_NATVEG": clean(surf["PCT_NATVEG"].values),
        "PCT_CROP": clean(surf["PCT_CROP"].values),
        "PCT_URBAN": np.nansum(clean(surf["PCT_URBAN"].values), axis=0),
        "PCT_LAKE": clean(surf["PCT_LAKE"].values),
        "PCT_WETLAND": clean(surf["PCT_WETLAND"].values),
        "PCT_GLACIER": clean(surf["PCT_GLACIER"].values),
    }
    landcover_groups = {
        "southeast_all_land": southeast_land,
        "other_all_land": other_land,
        "lowest_20pct_GPP": low20,
        "highest_20pct_GPP": high20,
        "florida_all_land": land & florida,
        "adjacent_north_all_land": land & adjacent_north,
        "adjacent_west_all_land": land & adjacent_west,
    }
    landcover_rows: list[dict[str, object]] = []
    for cover_name, cover_values in landcover_arrays.items():
        row: dict[str, object] = {"landcover": cover_name}
        for group_name, group_mask in landcover_groups.items():
            row[group_name] = weighted_mean(cover_values, weights, group_mask)
        row["southeast_minus_other_pct_points"] = (
            float(row["southeast_all_land"]) - float(row["other_all_land"])
        )
        row["lowest20_minus_highest20_pct_points"] = (
            float(row["lowest_20pct_GPP"]) - float(row["highest_20pct_GPP"])
        )
        landcover_rows.append(row)
    write_csv(OUT_DIR / "landcover_summary.csv", landcover_rows)

    pct_natveg = landcover_arrays["PCT_NATVEG"]
    pct_nat_pft = clean(surf["PCT_NAT_PFT"].values)
    if pct_nat_pft.shape[0] != len(PFT_NAMES):
        raise ValueError(
            f"Expected {len(PFT_NAMES)} natural PFTs, found {pct_nat_pft.shape[0]}"
        )
    pft_rows: list[dict[str, object]] = []
    for pft_index, pft_name in enumerate(PFT_NAMES):
        within_natveg = pct_nat_pft[pft_index]
        effective_land_pct = pct_natveg * within_natveg / 100.0
        pft_row: dict[str, object] = {
            "pft_index": pft_index,
            "pft_name": pft_name,
        }
        for group_name, group_mask in landcover_groups.items():
            pft_row[f"{group_name}_within_natveg_pct"] = weighted_mean(
                within_natveg, weights, group_mask
            )
            pft_row[f"{group_name}_effective_land_pct"] = weighted_mean(
                effective_land_pct, weights, group_mask
            )
        pft_row["southeast_minus_other_effective_pct_points"] = (
            float(pft_row["southeast_all_land_effective_land_pct"])
            - float(pft_row["other_all_land_effective_land_pct"])
        )
        pft_row["lowest20_minus_highest20_effective_pct_points"] = (
            float(pft_row["lowest_20pct_GPP_effective_land_pct"])
            - float(pft_row["highest_20pct_GPP_effective_land_pct"])
        )
        pft_rows.append(pft_row)
    write_csv(OUT_DIR / "pft_summary.csv", pft_rows)

    landcover_total = np.zeros_like(pct_natveg)
    for cover_values in landcover_arrays.values():
        landcover_total = landcover_total + cover_values

    time_bounds = clean(ds["time_bounds"].isel(time=0).values)
    interval_days = float(time_bounds[-1] - time_bounds[0])
    quality = {
        "source": str(NC_PATH),
        "surface_source": str(SURFDATA_PATH),
        "grid_shape": [int(lat.size), int(lon.size)],
        "interval_days": interval_days,
        "interval_years_365_day_calendar": interval_days / 365.0,
        "plot_scale_issue": (
            "The existing map multiplies mean GPP by the full interval; "
            "annual GPP should multiply by 365 days instead. Spatial ranking is unchanged."
        ),
        "region_definition": "lon >= -85.5 and lat <= 32.5",
        "florida_definition": "lon >= -83.5 and lat <= 30.5",
        "adjacent_north_definition": "lon >= -85.5 and 30.5 < lat <= 33.5",
        "adjacent_west_definition": "-88 <= lon < -83.5 and lat <= 30.5",
        "land_definition": "landmask == 1 and landfrac >= 0.5",
        "vegetated_definition": "land definition and TLAI > 0.1",
        "land_cells": int(np.count_nonzero(land)),
        "vegetated_cells": int(np.count_nonzero(vegetated)),
        "southeast_land_cells": int(np.count_nonzero(southeast_land)),
        "southeast_vegetated_cells": int(np.count_nonzero(southeast_vegetated)),
        "gpp_vegetated_q20_gC_m2_yr": float(q20),
        "gpp_vegetated_q80_gC_m2_yr": float(q80),
        "surface_grid_shape": [int(pct_natveg.shape[0]), int(pct_natveg.shape[1])],
        "mean_landcover_sum_pct": weighted_mean(landcover_total, weights, land),
        "max_abs_landcover_sum_error_pct": float(
            np.nanmax(np.abs(np.where(land, landcover_total, np.nan) - 100.0))
        ),
    }
    with (OUT_DIR / "quality_summary.json").open("w") as handle:
        json.dump(quality, handle, indent=2)

    ds.close()
    surf.close()
    print(json.dumps(quality, indent=2))
    print(f"Wrote diagnostic tables to {OUT_DIR}")


if __name__ == "__main__":
    main()
