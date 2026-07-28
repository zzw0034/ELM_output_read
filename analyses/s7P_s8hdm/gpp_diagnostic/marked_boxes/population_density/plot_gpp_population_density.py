#!/usr/bin/env python
"""Compare ELM GPP and human population density in the marked boxes."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import numpy as np
import xarray as xr


NC_PATH = Path(os.environ["NC_PATH"])
OUT_DIR = Path(os.environ["OUT_DIR"])
SECONDS_PER_YEAR = 365.0 * 86400.0
FILL_LIMIT = 1.0e30
RING_WIDTH_DEGREES = 0.75

BOXES = {
    "upper": {"lon_min": -85.5, "lon_max": -82.2, "lat_min": 30.7, "lat_max": 32.9},
    "lower": {"lon_min": -86.3, "lon_max": -80.4, "lat_min": 27.5, "lat_max": 30.5},
}


def clean(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    result[~np.isfinite(result) | (np.abs(result) >= FILL_LIMIT)] = np.nan
    return result


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


def add_boxes(axis: plt.Axes) -> None:
    for name, bounds in BOXES.items():
        axis.add_patch(
            Rectangle(
                (bounds["lon_min"], bounds["lat_min"]),
                bounds["lon_max"] - bounds["lon_min"],
                bounds["lat_max"] - bounds["lat_min"],
                fill=False,
                edgecolor="#d62728",
                linewidth=1.5,
                zorder=5,
            )
        )
        axis.text(
            bounds["lon_min"] + 0.08,
            bounds["lat_max"] + 0.08,
            f"{name.title()} box",
            color="#b11f24",
            fontsize=8,
            weight="bold",
            zorder=6,
        )


def configure_map(axis: plt.Axes, lon: np.ndarray, lat: np.ndarray) -> None:
    axis.set_xlim(float(np.nanmin(lon)), float(np.nanmax(lon)))
    axis.set_ylim(float(np.nanmin(lat)), float(np.nanmax(lat)))
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.grid(color="0.85", linewidth=0.35, alpha=0.6)
    add_boxes(axis)


def weighted_mean(values: np.ndarray, weights: np.ndarray, mask: np.ndarray) -> float:
    valid = mask & np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(valid):
        return float("nan")
    return float(np.average(values[valid], weights=weights[valid]))


def weighted_share(condition: np.ndarray, weights: np.ndarray, mask: np.ndarray) -> float:
    valid = mask & np.isfinite(weights) & (weights > 0)
    denominator = float(np.sum(weights[valid]))
    if denominator == 0:
        return float("nan")
    return float(np.sum(weights[valid & condition]) / denominator)


def pearson(x: np.ndarray, y: np.ndarray, mask: np.ndarray) -> tuple[float, int]:
    valid = mask & np.isfinite(x) & np.isfinite(y)
    count = int(np.count_nonzero(valid))
    if count < 3 or np.nanstd(x[valid]) == 0 or np.nanstd(y[valid]) == 0:
        return float("nan"), count
    return float(np.corrcoef(x[valid], y[valid])[0, 1]), count


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_maps(
    lon: np.ndarray,
    lat: np.ndarray,
    gpp: np.ndarray,
    population: np.ndarray,
    output_path: Path,
) -> None:
    valid_gpp = gpp[np.isfinite(gpp)]
    valid_population = population[np.isfinite(population)]
    gpp_vmax = float(np.nanquantile(valid_gpp, 0.995))
    pop_log = np.log10(1.0 + np.maximum(population, 0.0))
    pop_vmax_data = float(
        np.nanquantile(np.log10(1.0 + np.maximum(valid_population, 0.0)), 0.995)
    )
    population_has_variation = float(np.nanmax(valid_population)) > float(
        np.nanmin(valid_population)
    )
    pop_vmax = pop_vmax_data if pop_vmax_data > 0 else 1.0

    figure, axes = plt.subplots(1, 2, figsize=(15.2, 6.3), constrained_layout=True)
    gpp_mesh = axes[0].pcolormesh(
        lon, lat, gpp, shading="auto", cmap="YlGn", vmin=0, vmax=gpp_vmax
    )
    configure_map(axes[0], lon, lat)
    axes[0].set_title("GPP")
    gpp_bar = figure.colorbar(gpp_mesh, ax=axes[0], shrink=0.88, pad=0.02, extend="max")
    gpp_bar.set_label("gC m⁻² yr⁻¹ (7300-day mean annualized)")

    pop_mesh = axes[1].pcolormesh(
        lon, lat, pop_log, shading="auto", cmap="magma", vmin=0, vmax=pop_vmax
    )
    configure_map(axes[1], lon, lat)
    axes[1].set_title("Human population density (HDM)")
    pop_bar = figure.colorbar(pop_mesh, ax=axes[1], shrink=0.88, pad=0.02, extend="max")
    tick_values = np.asarray([0, 1, 10, 100, 1000, 10000], dtype=float)
    tick_positions = np.log10(1.0 + tick_values)
    keep = tick_positions <= pop_vmax + 1.0e-9
    pop_bar.set_ticks(tick_positions[keep])
    pop_bar.set_ticklabels([f"{value:g}" for value in tick_values[keep]])
    pop_bar.set_label("counts km⁻² (log color scale)")
    if not population_has_variation:
        pop_bar.set_ticks([0])
        pop_bar.set_ticklabels([f"{float(valid_population[0]):g}"])
        axes[1].text(
            0.5,
            0.5,
            "HDM = 0 counts km⁻²\nat every valid land grid cell",
            transform=axes[1].transAxes,
            ha="center",
            va="center",
            fontsize=12,
            weight="bold",
            bbox={"facecolor": "white", "edgecolor": "0.75", "alpha": 0.9},
            zorder=7,
        )

    figure.suptitle("GPP and human population density over the Southeast ELM domain", fontsize=15)
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def add_binned_median(axis: plt.Axes, population: np.ndarray, gpp: np.ndarray) -> None:
    x = np.log10(1.0 + population)
    if len(x) < 10:
        return
    edges = np.unique(np.nanquantile(x, np.linspace(0, 1, 11)))
    centers: list[float] = []
    medians: list[float] = []
    for left, right in zip(edges[:-1], edges[1:]):
        select = (x >= left) & (x <= right if right == edges[-1] else x < right)
        if np.count_nonzero(select) >= 5:
            centers.append(float(np.nanmedian(x[select])))
            medians.append(float(np.nanmedian(gpp[select])))
    if centers:
        axis.plot(centers, medians, color="#d62728", marker="o", markersize=4, linewidth=1.5,
                  label="Population-decile median GPP")
        axis.legend(loc="best", frameon=False, fontsize=8)


def plot_scatter(
    gpp: np.ndarray,
    population: np.ndarray,
    group_masks: dict[str, np.ndarray],
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13.5, 5.7), sharey=True, constrained_layout=True)
    for axis, name in zip(axes, BOXES):
        mask = group_masks[f"{name}_box"] & np.isfinite(gpp) & np.isfinite(population)
        x = np.log10(1.0 + np.maximum(population[mask], 0.0))
        y = gpp[mask]
        has_variation = float(np.nanmax(x)) > float(np.nanmin(x))
        axis.scatter(x, y, s=8, alpha=0.22, color="#355c9a", linewidths=0, rasterized=True)
        if has_variation:
            add_binned_median(axis, np.maximum(population[mask], 0.0), y)
        correlation, count = pearson(gpp, np.log1p(np.maximum(population, 0.0)), mask)
        axis.text(
            0.02,
            0.98,
            f"Pearson r(GPP, ln(1+HDM)) = {correlation:.3f}\nn = {count:,} grid cells",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "0.8", "alpha": 0.88},
        )
        axis.set_title(f"{name.title()} box")
        axis.set_xlabel("Population density (counts km⁻²; log₁₀(1+x) axis)")
        axis.grid(color="0.88", linewidth=0.4)
        ticks = np.asarray([0, 1, 10, 100, 1000, 10000], dtype=float)
        axis.set_xticks(np.log10(1.0 + ticks))
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{10**value - 1:.0f}"))
        if not has_variation:
            axis.set_xlim(-0.02, 0.25)
            axis.set_xticks([0])
            axis.set_xticklabels(["0"])
            axis.text(
                0.5,
                0.5,
                "No HDM variation; spatial correlation\ncannot be calculated",
                transform=axis.transAxes,
                ha="center",
                va="center",
                fontsize=11,
                weight="bold",
                bbox={"facecolor": "white", "edgecolor": "0.75", "alpha": 0.9},
            )
    axes[0].set_ylabel("GPP (gC m⁻² yr⁻¹; 7300-day mean annualized)")
    figure.suptitle("Grid-cell relationship between GPP and human population density", fontsize=14)
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(NC_PATH, decode_times=False)
    required = {"GPP", "HDM", "lat", "lon", "area", "landfrac", "landmask"}
    missing = sorted(required.difference(ds.variables))
    if missing:
        raise KeyError(f"Missing history variables: {missing}")

    lon = clean(ds["lon"].values)
    lat = clean(ds["lat"].values)
    lon2d, lat2d = np.meshgrid(lon, lat)
    area = clean(ds["area"].values)
    landfrac = clean(ds["landfrac"].values)
    weights = area * landfrac
    gpp = clean(ds["GPP"].isel(time=0).values) * SECONDS_PER_YEAR
    population = clean(ds["HDM"].isel(time=0).values)
    land = (
        (np.asarray(ds["landmask"].values) == 1)
        & np.isfinite(landfrac)
        & (landfrac >= 0.5)
        & np.isfinite(gpp)
        & np.isfinite(population)
        & (population >= 0)
    )

    raw_boxes = {name: bounds_mask(lon2d, lat2d, bounds) for name, bounds in BOXES.items()}
    any_box = np.logical_or.reduce(tuple(raw_boxes.values()))
    group_masks: dict[str, np.ndarray] = {}
    rows: list[dict[str, object]] = []
    for name, bounds in BOXES.items():
        box = land & raw_boxes[name]
        ring = land & bounds_mask(lon2d, lat2d, expanded(bounds)) & ~any_box
        group_masks[f"{name}_box"] = box
        group_masks[f"{name}_ring"] = ring
        box_low_gpp_threshold = float(np.nanquantile(gpp[box], 0.30))
        box_high_pop_threshold = float(np.nanquantile(population[box], 0.70))
        population_min = float(np.nanmin(population[box]))
        population_max = float(np.nanmax(population[box]))
        population_has_variation = population_max > population_min
        for group_name, mask in (("box", box), ("ring", ring)):
            correlation_raw, count = pearson(gpp, population, mask)
            correlation_log, _ = pearson(gpp, np.log1p(population), mask)
            rows.append(
                {
                    "box": name,
                    "group": group_name,
                    "n_cells": count,
                    "area_weighted_GPP_gC_m2_yr": weighted_mean(gpp, weights, mask),
                    "area_weighted_population_counts_km2": weighted_mean(population, weights, mask),
                    "population_median_counts_km2": float(np.nanmedian(population[mask])),
                    "population_p90_counts_km2": float(np.nanquantile(population[mask], 0.90)),
                    "population_min_counts_km2": float(np.nanmin(population[mask])),
                    "population_max_counts_km2": float(np.nanmax(population[mask])),
                    "population_variation_available": population_has_variation,
                    "area_share_population_gt_100": weighted_share(population > 100, weights, mask),
                    "pearson_GPP_population": correlation_raw,
                    "pearson_GPP_log1p_population": correlation_log,
                    "low_GPP30_threshold_gC_m2_yr": box_low_gpp_threshold,
                    "high_population30_threshold_counts_km2": box_high_pop_threshold,
                    "high_population_cells_that_are_low_GPP30": (
                        weighted_share(
                            gpp <= box_low_gpp_threshold,
                            weights,
                            mask & (population >= box_high_pop_threshold),
                        )
                        if population_has_variation
                        else float("nan")
                    ),
                }
            )

    write_csv(OUT_DIR / "gpp_population_density_summary.csv", rows)
    plot_maps(
        lon,
        lat,
        np.where(land, gpp, np.nan),
        np.where(land, population, np.nan),
        OUT_DIR / "gpp_population_density_maps.png",
    )
    plot_scatter(gpp, population, group_masks, OUT_DIR / "gpp_population_density_scatter.png")

    metadata = {
        "history_file": str(NC_PATH),
        "population_variable": "HDM",
        "population_long_name": str(ds["HDM"].attrs.get("long_name", "")),
        "population_units": str(ds["HDM"].attrs.get("units", "")),
        "gpp_units_source": str(ds["GPP"].attrs.get("units", "")),
        "gpp_conversion": "multiplied by 365*86400 to annualize the 7300-day time mean",
        "ring_width_degrees": RING_WIDTH_DEGREES,
        "boxes": BOXES,
        "valid_land_population_min_counts_km2": float(np.nanmin(population[land])),
        "valid_land_population_max_counts_km2": float(np.nanmax(population[land])),
        "valid_land_population_variation_available": bool(
            float(np.nanmax(population[land])) > float(np.nanmin(population[land]))
        ),
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    ds.close()
    for path in sorted(OUT_DIR.iterdir()):
        print(path)


if __name__ == "__main__":
    main()
