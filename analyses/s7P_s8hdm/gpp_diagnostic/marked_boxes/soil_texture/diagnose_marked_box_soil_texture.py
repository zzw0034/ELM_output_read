#!/usr/bin/env python
"""Compare soil texture and terrain in two marked GPP boxes and nearby rings."""

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
FILL_LIMIT = 1.0e30
SECONDS_PER_YEAR = 365.0 * 86400.0
RING_WIDTH_DEGREES = 0.75

BOXES = {
    "upper": {"lon_min": -85.5, "lon_max": -82.2, "lat_min": 30.7, "lat_max": 32.9},
    "lower": {"lon_min": -86.3, "lon_max": -80.4, "lat_min": 27.5, "lat_max": 30.5},
}
PROFILE_VARIABLES = ("PCT_SAND", "PCT_CLAY", "ORGANIC")
TERRAIN_VARIABLES = ("SLOPE", "TOPO", "STD_ELEV")
CATEGORICAL_VARIABLES = ("SOIL_ORDER", "SOIL_COLOR")


def clean(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    result[~np.isfinite(result) | (np.abs(result) >= FILL_LIMIT)] = np.nan
    return result


def weighted_mean(values: np.ndarray, weights: np.ndarray, mask: np.ndarray) -> float:
    valid = mask & np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(valid):
        return float("nan")
    return float(np.average(values[valid], weights=weights[valid]))


def weighted_std(values: np.ndarray, weights: np.ndarray, mask: np.ndarray) -> float:
    valid = mask & np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(valid):
        return float("nan")
    mean = np.average(values[valid], weights=weights[valid])
    variance = np.average((values[valid] - mean) ** 2, weights=weights[valid])
    return float(np.sqrt(variance))


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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def pearson(values: np.ndarray, gpp: np.ndarray, mask: np.ndarray) -> tuple[float, int]:
    valid = mask & np.isfinite(values) & np.isfinite(gpp)
    count = int(np.count_nonzero(valid))
    if count < 3 or np.nanstd(values[valid]) == 0 or np.nanstd(gpp[valid]) == 0:
        return float("nan"), count
    return float(np.corrcoef(values[valid], gpp[valid])[0, 1]), count


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    history = xr.open_dataset(NC_PATH, decode_times=False)
    surf = xr.open_dataset(SURFDATA_PATH, decode_times=False)

    required_history = {"GPP", "lat", "lon", "area", "landfrac", "landmask"}
    required_surface = {*PROFILE_VARIABLES, *TERRAIN_VARIABLES, *CATEGORICAL_VARIABLES}
    missing_history = sorted(required_history.difference(history.variables))
    missing_surface = sorted(required_surface.difference(surf.variables))
    if missing_history or missing_surface:
        raise KeyError(f"Missing variables: history={missing_history}, surface={missing_surface}")

    lat = clean(history["lat"].values)
    lon = clean(history["lon"].values)
    lon2d, lat2d = np.meshgrid(lon, lat)
    area = clean(history["area"].values)
    landfrac = clean(history["landfrac"].values)
    weights = area * landfrac
    gpp = clean(history["GPP"].isel(time=0).values) * SECONDS_PER_YEAR
    land = (
        (np.asarray(history["landmask"].values) == 1)
        & np.isfinite(landfrac)
        & (landfrac >= 0.5)
        & np.isfinite(gpp)
    )

    raw_boxes = {name: bounds_mask(lon2d, lat2d, bounds) for name, bounds in BOXES.items()}
    any_box = np.logical_or.reduce(tuple(raw_boxes.values()))
    groups: dict[str, np.ndarray] = {}
    for name, bounds in BOXES.items():
        box = land & raw_boxes[name]
        ring = land & bounds_mask(lon2d, lat2d, expanded(bounds)) & ~any_box
        q30 = float(np.nanquantile(gpp[box], 0.30))
        groups[f"{name}_box"] = box
        groups[f"{name}_ring"] = ring
        groups[f"{name}_box_low30"] = box & (gpp <= q30)

    profile_arrays = {name: clean(surf[name].values) for name in PROFILE_VARIABLES}
    nlevsoi = int(profile_arrays["PCT_SAND"].shape[0])
    if any(values.shape != (nlevsoi, lat.size, lon.size) for values in profile_arrays.values()):
        raise ValueError("Soil profile dimensions do not align with the history grid")

    profile_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []
    correlation_rows: list[dict[str, object]] = []
    for variable, profile in profile_arrays.items():
        units = str(surf[variable].attrs.get("units", ""))
        for layer in range(nlevsoi):
            values = profile[layer]
            row: dict[str, object] = {"variable": variable, "units": units, "soil_layer_index": layer}
            for group_name, group_mask in groups.items():
                row[f"{group_name}_mean"] = weighted_mean(values, weights, group_mask)
                row[f"{group_name}_std"] = weighted_std(values, weights, group_mask)
            profile_rows.append(row)

            for box_name in BOXES:
                box_mean = float(row[f"{box_name}_box_mean"])
                ring_mean = float(row[f"{box_name}_ring_mean"])
                ring_std = float(row[f"{box_name}_ring_std"])
                low30_mean = float(row[f"{box_name}_box_low30_mean"])
                comparison_rows.append(
                    {
                        "box": box_name,
                        "variable": variable,
                        "units": units,
                        "soil_layer_index": layer,
                        "box_mean": box_mean,
                        "ring_mean": ring_mean,
                        "box_minus_ring": box_mean - ring_mean,
                        "box_minus_ring_pct": 100.0 * (box_mean / ring_mean - 1.0) if ring_mean != 0 else float("nan"),
                        "standardized_difference_vs_ring_std": (box_mean - ring_mean) / ring_std if ring_std > 0 else float("nan"),
                        "box_low30_mean": low30_mean,
                        "low30_minus_ring": low30_mean - ring_mean,
                    }
                )
                for scope in ("box", "ring", "box_low30"):
                    group_name = f"{box_name}_{scope}"
                    corr, count = pearson(values, gpp, groups[group_name])
                    correlation_rows.append(
                        {
                            "box": box_name,
                            "scope": scope,
                            "variable": variable,
                            "soil_layer_index": layer,
                            "pearson_r_with_GPP": corr,
                            "n_cells": count,
                        }
                    )
    write_csv(OUT_DIR / "soil_profile_summary.csv", profile_rows)
    write_csv(OUT_DIR / "soil_box_ring_comparison.csv", comparison_rows)
    write_csv(OUT_DIR / "soil_gpp_correlations.csv", correlation_rows)

    terrain_rows: list[dict[str, object]] = []
    for variable in TERRAIN_VARIABLES:
        values = clean(surf[variable].values)
        row: dict[str, object] = {
            "variable": variable,
            "units": str(surf[variable].attrs.get("units", "")),
        }
        for group_name, group_mask in groups.items():
            row[f"{group_name}_mean"] = weighted_mean(values, weights, group_mask)
            row[f"{group_name}_std"] = weighted_std(values, weights, group_mask)
        for box_name in BOXES:
            box_mean = float(row[f"{box_name}_box_mean"])
            ring_mean = float(row[f"{box_name}_ring_mean"])
            ring_std = float(row[f"{box_name}_ring_std"])
            row[f"{box_name}_box_minus_ring"] = box_mean - ring_mean
            row[f"{box_name}_standardized_difference"] = (
                (box_mean - ring_mean) / ring_std if ring_std > 0 else float("nan")
            )
        terrain_rows.append(row)
    write_csv(OUT_DIR / "terrain_summary.csv", terrain_rows)

    categorical_rows: list[dict[str, object]] = []
    for variable in CATEGORICAL_VARIABLES:
        values = clean(surf[variable].values)
        codes = sorted(int(code) for code in np.unique(values[land & np.isfinite(values)]))
        for code in codes:
            row: dict[str, object] = {"variable": variable, "code": code}
            for group_name, group_mask in groups.items():
                denominator = weighted_mean(np.ones_like(values), weights, group_mask)
                numerator = weighted_mean((values == code).astype(float), weights, group_mask)
                row[f"{group_name}_share_pct"] = 100.0 * numerator / denominator if denominator else float("nan")
            categorical_rows.append(row)
    write_csv(OUT_DIR / "soil_category_summary.csv", categorical_rows)

    quality = {
        "history_source": str(NC_PATH),
        "surface_source": str(SURFDATA_PATH),
        "grid_shape": [int(lat.size), int(lon.size)],
        "nlevsoi": nlevsoi,
        "profile_variables": list(PROFILE_VARIABLES),
        "terrain_variables": list(TERRAIN_VARIABLES),
        "categorical_variables": list(CATEGORICAL_VARIABLES),
        "box_bounds": BOXES,
        "ring_width_degrees": RING_WIDTH_DEGREES,
        "group_cell_counts": {name: int(np.count_nonzero(mask)) for name, mask in groups.items()},
        "profile_ranges": {
            name: {"min": float(np.nanmin(values[:, land])), "max": float(np.nanmax(values[:, land]))}
            for name, values in profile_arrays.items()
        },
    }
    with (OUT_DIR / "quality_summary.json").open("w") as handle:
        json.dump(quality, handle, indent=2)

    history.close()
    surf.close()
    print(json.dumps(quality, indent=2))
    print(f"Wrote soil-texture diagnostics to {OUT_DIR}")


if __name__ == "__main__":
    main()
