#!/usr/bin/env python
"""Diagnose the two user-marked low-GPP boxes against nearby land rings."""

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
RING_WIDTH_DEGREES = 0.75

BOXES = {
    "upper": {"lon_min": -85.5, "lon_max": -82.2, "lat_min": 30.7, "lat_max": 32.9},
    "lower": {"lon_min": -86.3, "lon_max": -80.4, "lat_min": 27.5, "lat_max": 30.5},
}

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


def bounds_mask(lon2d: np.ndarray, lat2d: np.ndarray, bounds: dict[str, float]) -> np.ndarray:
    return (
        (lon2d >= bounds["lon_min"])
        & (lon2d <= bounds["lon_max"])
        & (lat2d >= bounds["lat_min"])
        & (lat2d <= bounds["lat_max"])
    )


def expanded(bounds: dict[str, float]) -> dict[str, float]:
    return {
        "lon_min": bounds["lon_min"] - RING_WIDTH_DEGREES,
        "lon_max": bounds["lon_max"] + RING_WIDTH_DEGREES,
        "lat_min": bounds["lat_min"] - RING_WIDTH_DEGREES,
        "lat_max": bounds["lat_max"] + RING_WIDTH_DEGREES,
    }


def summarize_group(
    group: str,
    mask: np.ndarray,
    weights: np.ndarray,
    arrays: dict[str, np.ndarray],
) -> dict[str, object]:
    gpp = arrays["GPP_gC_m2_yr"]
    valid_gpp = mask & np.isfinite(gpp)
    row: dict[str, object] = {
        "group": group,
        "n_cells": int(np.count_nonzero(mask)),
        "area_weight_sum_km2": float(np.nansum(np.where(mask, weights, np.nan))),
    }
    for name in OUTPUT_NAMES:
        row[name] = weighted_mean(arrays[name], weights, mask)
    row["GPP_median_gC_m2_yr"] = float(np.nanmedian(np.where(mask, gpp, np.nan)))
    row["GPP_q10_gC_m2_yr"] = float(np.nanquantile(gpp[valid_gpp], 0.10))
    row["GPP_q30_gC_m2_yr"] = float(np.nanquantile(gpp[valid_gpp], 0.30))
    row["near_zero_GPP_share"] = float(
        np.count_nonzero(valid_gpp & (gpp < 1.0)) / max(np.count_nonzero(valid_gpp), 1)
    )
    return row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def correlation_rows(
    group: str, mask: np.ndarray, arrays: dict[str, np.ndarray]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    gpp = arrays["GPP_gC_m2_yr"]
    for driver in OUTPUT_NAMES[1:]:
        values = arrays[driver]
        valid = mask & np.isfinite(gpp) & np.isfinite(values)
        count = int(np.count_nonzero(valid))
        corr = float(np.corrcoef(gpp[valid], values[valid])[0, 1]) if count >= 3 else float("nan")
        rows.append(
            {
                "group": group,
                "driver": driver,
                "pearson_r_with_GPP": corr,
                "n_cells": count,
            }
        )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(NC_PATH, decode_times=False)
    required = {
        "GPP", "TLAI", "BTRAN", "FPG", "FPG_P", "FSDS", "TBOT", "TOTVEGC",
        "lat", "lon", "area", "landfrac", "landmask",
    }
    missing = sorted(required.difference(ds.variables))
    if missing:
        raise KeyError(f"Missing history variables: {missing}")

    lat = clean(ds["lat"].values)
    lon = clean(ds["lon"].values)
    lon2d, lat2d = np.meshgrid(lon, lat)
    area = clean(ds["area"].values)
    landfrac = clean(ds["landfrac"].values)
    weights = area * landfrac
    arrays = {
        "GPP_gC_m2_yr": clean(ds["GPP"].isel(time=0).values) * SECONDS_PER_YEAR,
        "TLAI": clean(ds["TLAI"].isel(time=0).values),
        "BTRAN": clean(ds["BTRAN"].isel(time=0).values),
        "FPG": clean(ds["FPG"].isel(time=0).values),
        "FPG_P": clean(ds["FPG_P"].isel(time=0).values),
        "FSDS_W_m2": clean(ds["FSDS"].isel(time=0).values),
        "TBOT_C": clean(ds["TBOT"].isel(time=0).values) - 273.15,
        "TOTVEGC_gC_m2": clean(ds["TOTVEGC"].isel(time=0).values),
    }
    land = (
        (np.asarray(ds["landmask"].values) == 1)
        & np.isfinite(landfrac)
        & (landfrac >= 0.5)
        & np.isfinite(arrays["GPP_gC_m2_yr"])
    )

    raw_box_masks = {name: bounds_mask(lon2d, lat2d, bounds) for name, bounds in BOXES.items()}
    any_box = np.logical_or.reduce(tuple(raw_box_masks.values()))
    groups: dict[str, np.ndarray] = {}
    for name, bounds in BOXES.items():
        box = land & raw_box_masks[name]
        ring = land & bounds_mask(lon2d, lat2d, expanded(bounds)) & ~any_box
        threshold = float(np.nanquantile(arrays["GPP_gC_m2_yr"][box], 0.30))
        groups[f"{name}_box"] = box
        groups[f"{name}_ring"] = ring
        groups[f"{name}_box_low30"] = box & (arrays["GPP_gC_m2_yr"] <= threshold)

    region_rows = [summarize_group(name, mask, weights, arrays) for name, mask in groups.items()]
    write_csv(OUT_DIR / "region_summary.csv", region_rows)

    region_by_name = {str(row["group"]): row for row in region_rows}
    comparison_rows: list[dict[str, object]] = []
    for name in BOXES:
        box_row = region_by_name[f"{name}_box"]
        ring_row = region_by_name[f"{name}_ring"]
        for metric in OUTPUT_NAMES:
            box_value = float(box_row[metric])
            ring_value = float(ring_row[metric])
            comparison_rows.append(
                {
                    "box": name,
                    "metric": metric,
                    "box_value": box_value,
                    "ring_value": ring_value,
                    "box_minus_ring": box_value - ring_value,
                    "box_minus_ring_pct": 100.0 * (box_value / ring_value - 1.0) if ring_value != 0 else float("nan"),
                    "box_as_pct_of_ring": 100.0 * box_value / ring_value if ring_value != 0 else float("nan"),
                }
            )
    write_csv(OUT_DIR / "box_ring_comparison.csv", comparison_rows)

    correlations: list[dict[str, object]] = []
    for name in BOXES:
        correlations.extend(correlation_rows(f"{name}_box", groups[f"{name}_box"], arrays))
        correlations.extend(correlation_rows(f"{name}_ring", groups[f"{name}_ring"], arrays))
    write_csv(OUT_DIR / "driver_correlations.csv", correlations)

    surf = xr.open_dataset(SURFDATA_PATH, decode_times=False)
    surface_required = {
        "PCT_NAT_PFT", "PCT_NATVEG", "PCT_CROP", "PCT_URBAN", "PCT_LAKE",
        "PCT_WETLAND", "PCT_GLACIER",
    }
    surface_missing = sorted(surface_required.difference(surf.variables))
    if surface_missing:
        raise KeyError(f"Missing surface variables: {surface_missing}")

    landcover_arrays = {
        "PCT_NATVEG": clean(surf["PCT_NATVEG"].values),
        "PCT_CROP": clean(surf["PCT_CROP"].values),
        "PCT_URBAN": np.nansum(clean(surf["PCT_URBAN"].values), axis=0),
        "PCT_LAKE": clean(surf["PCT_LAKE"].values),
        "PCT_WETLAND": clean(surf["PCT_WETLAND"].values),
        "PCT_GLACIER": clean(surf["PCT_GLACIER"].values),
    }
    landcover_rows: list[dict[str, object]] = []
    for cover_name, values in landcover_arrays.items():
        row: dict[str, object] = {"landcover": cover_name}
        for group_name, group_mask in groups.items():
            row[group_name] = weighted_mean(values, weights, group_mask)
        for name in BOXES:
            row[f"{name}_box_minus_ring_pct_points"] = (
                float(row[f"{name}_box"]) - float(row[f"{name}_ring"])
            )
        landcover_rows.append(row)
    write_csv(OUT_DIR / "landcover_summary.csv", landcover_rows)

    pct_natveg = landcover_arrays["PCT_NATVEG"]
    pct_nat_pft = clean(surf["PCT_NAT_PFT"].values)
    if pct_nat_pft.shape[0] != len(PFT_NAMES):
        raise ValueError(f"Expected {len(PFT_NAMES)} natural PFTs, found {pct_nat_pft.shape[0]}")
    pft_rows: list[dict[str, object]] = []
    for pft_index, pft_name in enumerate(PFT_NAMES):
        within_natveg = pct_nat_pft[pft_index]
        effective_land_pct = pct_natveg * within_natveg / 100.0
        row: dict[str, object] = {"pft_index": pft_index, "pft_name": pft_name}
        for group_name, group_mask in groups.items():
            row[f"{group_name}_within_natveg_pct"] = weighted_mean(within_natveg, weights, group_mask)
            row[f"{group_name}_effective_land_pct"] = weighted_mean(effective_land_pct, weights, group_mask)
        for name in BOXES:
            row[f"{name}_box_minus_ring_effective_pct_points"] = (
                float(row[f"{name}_box_effective_land_pct"])
                - float(row[f"{name}_ring_effective_land_pct"])
            )
        pft_rows.append(row)
    write_csv(OUT_DIR / "pft_summary.csv", pft_rows)

    landcover_total = np.zeros_like(pct_natveg)
    for values in landcover_arrays.values():
        landcover_total += values
    time_bounds = clean(ds["time_bounds"].isel(time=0).values)
    quality = {
        "history_source": str(NC_PATH),
        "surface_source": str(SURFDATA_PATH),
        "grid_shape": [int(lat.size), int(lon.size)],
        "interval_days": float(time_bounds[-1] - time_bounds[0]),
        "annualization": "GPP mean flux multiplied by 365 days; map pattern is unchanged from full-interval scaling",
        "box_bounds": BOXES,
        "ring_width_degrees": RING_WIDTH_DEGREES,
        "ring_definition": "expanded rectangle minus both marked boxes; landmask==1 and landfrac>=0.5",
        "group_cell_counts": {name: int(np.count_nonzero(mask)) for name, mask in groups.items()},
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
    print(f"Wrote marked-box diagnostics to {OUT_DIR}")


if __name__ == "__main__":
    main()
