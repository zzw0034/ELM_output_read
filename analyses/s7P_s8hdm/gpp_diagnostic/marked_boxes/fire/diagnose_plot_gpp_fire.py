#!/usr/bin/env python
"""Diagnose whether fire carbon loss shares the marked low-GPP pattern."""

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


def plot_maps(
    lon: np.ndarray,
    lat: np.ndarray,
    gpp: np.ndarray,
    fire: np.ndarray,
    output_path: Path,
) -> None:
    gpp_vmax = float(np.nanquantile(gpp[np.isfinite(gpp)], 0.995))
    fire_log = np.log10(1.0 + np.maximum(fire, 0.0))
    fire_vmax = float(np.nanquantile(fire_log[np.isfinite(fire_log)], 0.995))
    fire_vmax = max(fire_vmax, 1.0e-6)

    figure, axes = plt.subplots(1, 2, figsize=(15.2, 6.3), constrained_layout=True)
    gpp_mesh = axes[0].pcolormesh(
        lon, lat, gpp, shading="auto", cmap="YlGn", vmin=0, vmax=gpp_vmax
    )
    configure_map(axes[0], lon, lat)
    axes[0].set_title("GPP")
    gpp_bar = figure.colorbar(gpp_mesh, ax=axes[0], shrink=0.88, pad=0.02, extend="max")
    gpp_bar.set_label("gC m⁻² yr⁻¹ (7300-day mean annualized)")

    fire_mesh = axes[1].pcolormesh(
        lon, lat, fire_log, shading="auto", cmap="OrRd", vmin=0, vmax=fire_vmax
    )
    configure_map(axes[1], lon, lat)
    axes[1].set_title("Fire carbon loss (COL_FIRE_CLOSS)")
    fire_bar = figure.colorbar(fire_mesh, ax=axes[1], shrink=0.88, pad=0.02, extend="max")
    tick_values = np.asarray([0, 0.1, 1, 10, 100, 1000], dtype=float)
    tick_positions = np.log10(1.0 + tick_values)
    keep = tick_positions <= fire_vmax + 1.0e-9
    fire_bar.set_ticks(tick_positions[keep])
    fire_bar.set_ticklabels([f"{value:g}" for value in tick_values[keep]])
    fire_bar.set_label("gC m⁻² yr⁻¹ (log color scale)")

    figure.suptitle("GPP and fire carbon loss over the Southeast ELM domain", fontsize=15)
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def add_binned_median(axis: plt.Axes, fire: np.ndarray, gpp: np.ndarray) -> None:
    log_fire = np.log10(1.0 + fire)
    edges = np.unique(np.nanquantile(log_fire, np.linspace(0, 1, 11)))
    centers: list[float] = []
    medians: list[float] = []
    for left, right in zip(edges[:-1], edges[1:]):
        select = (
            (log_fire >= left)
            & (log_fire <= right if right == edges[-1] else log_fire < right)
        )
        if np.count_nonzero(select) >= 5:
            centers.append(float(np.nanmedian(fire[select])))
            medians.append(float(np.nanmedian(gpp[select])))
    if centers:
        axis.plot(
            centers,
            medians,
            color="#c23b22",
            marker="o",
            markersize=4,
            linewidth=1.5,
            label="Fire-decile median GPP",
        )
        axis.legend(loc="best", frameon=False, fontsize=8)


def plot_scatter(
    gpp: np.ndarray,
    fire: np.ndarray,
    group_masks: dict[str, np.ndarray],
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13.5, 5.7), sharey=True, constrained_layout=True)
    for axis, name in zip(axes, BOXES):
        mask = group_masks[f"{name}_box"] & np.isfinite(gpp) & np.isfinite(fire)
        x_raw = np.maximum(fire[mask], 0.0)
        y = gpp[mask]
        axis.scatter(
            x_raw, y, s=8, alpha=0.2, color="#355c9a", linewidths=0, rasterized=True
        )
        if np.nanmax(x_raw) > np.nanmin(x_raw):
            add_binned_median(axis, x_raw, y)
        correlation, count = pearson(gpp, np.log1p(np.maximum(fire, 0.0)), mask)
        axis.text(
            0.02,
            0.98,
            f"Pearson r(GPP, ln(1+fire)) = {correlation:.3f}\nn = {count:,} grid cells",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "0.8", "alpha": 0.88},
        )
        axis.set_title(f"{name.title()} box")
        axis.set_xlabel("Fire C loss (gC m⁻² yr⁻¹; symmetric log axis)")
        axis.set_xscale("symlog", linthresh=0.1, linscale=0.6)
        axis.grid(color="0.88", linewidth=0.4)
        ticks = np.asarray([0, 0.1, 1, 10, 100, 1000], dtype=float)
        keep = ticks <= float(np.nanmax(x_raw)) * 1.05 + 1.0e-9
        axis.set_xticks(ticks[keep])
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    axes[0].set_ylabel("GPP (gC m⁻² yr⁻¹; 7300-day mean annualized)")
    figure.suptitle("Grid-cell relationship between GPP and fire carbon loss", fontsize=14)
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def summarize_group(
    box_name: str,
    group_name: str,
    mask: np.ndarray,
    weights: np.ndarray,
    gpp: np.ndarray,
    fire: np.ndarray,
    tlai: np.ndarray,
    totvegc: np.ndarray,
) -> dict[str, object]:
    valid_fire = mask & np.isfinite(fire)
    gpp_mean = weighted_mean(gpp, weights, mask)
    fire_mean = weighted_mean(fire, weights, mask)
    return {
        "box": box_name,
        "group": group_name,
        "n_cells": int(np.count_nonzero(mask)),
        "area_weight_sum_km2": float(np.nansum(np.where(mask, weights, np.nan))),
        "GPP_gC_m2_yr": gpp_mean,
        "fire_C_loss_gC_m2_yr": fire_mean,
        "fire_C_loss_median_gC_m2_yr": float(np.nanmedian(fire[valid_fire])),
        "fire_C_loss_p90_gC_m2_yr": float(np.nanquantile(fire[valid_fire], 0.90)),
        "fire_nonzero_area_share": weighted_share(fire > 0, weights, mask),
        "fire_loss_as_pct_of_GPP": 100.0 * fire_mean / gpp_mean if gpp_mean != 0 else float("nan"),
        "TLAI": weighted_mean(tlai, weights, mask),
        "TOTVEGC_gC_m2": weighted_mean(totvegc, weights, mask),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(NC_PATH, decode_times=False)
    required = {
        "GPP", "COL_FIRE_CLOSS", "TLAI", "TOTVEGC",
        "lat", "lon", "area", "landfrac", "landmask",
    }
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
    fire = clean(ds["COL_FIRE_CLOSS"].isel(time=0).values) * SECONDS_PER_YEAR
    tlai = clean(ds["TLAI"].isel(time=0).values)
    totvegc = clean(ds["TOTVEGC"].isel(time=0).values)
    land = (
        (np.asarray(ds["landmask"].values) == 1)
        & np.isfinite(landfrac)
        & (landfrac >= 0.5)
        & np.isfinite(gpp)
        & np.isfinite(fire)
        & (fire >= 0)
    )

    raw_boxes = {name: bounds_mask(lon2d, lat2d, bounds) for name, bounds in BOXES.items()}
    any_box = np.logical_or.reduce(tuple(raw_boxes.values()))
    group_masks: dict[str, np.ndarray] = {}
    summary_rows: list[dict[str, object]] = []
    correlation_rows: list[dict[str, object]] = []
    for name, bounds in BOXES.items():
        box = land & raw_boxes[name]
        ring = land & bounds_mask(lon2d, lat2d, expanded(bounds)) & ~any_box
        low_threshold = float(np.nanquantile(gpp[box], 0.30))
        low30 = box & (gpp <= low_threshold)
        rest70 = box & (gpp > low_threshold)
        masks = {"box": box, "ring": ring, "low_GPP30": low30, "rest_GPP70": rest70}
        for group_name, mask in masks.items():
            group_masks[f"{name}_{group_name}"] = mask
            summary_rows.append(
                summarize_group(name, group_name, mask, weights, gpp, fire, tlai, totvegc)
            )
            fire_gpp, count = pearson(fire, gpp, mask)
            log_fire_gpp, _ = pearson(np.log1p(fire), gpp, mask)
            fire_tlai, _ = pearson(fire, tlai, mask)
            fire_vegc, _ = pearson(fire, totvegc, mask)
            correlation_rows.append(
                {
                    "box": name,
                    "group": group_name,
                    "n_cells": count,
                    "pearson_fire_GPP": fire_gpp,
                    "pearson_log1p_fire_GPP": log_fire_gpp,
                    "pearson_fire_TLAI": fire_tlai,
                    "pearson_fire_TOTVEGC": fire_vegc,
                }
            )

    write_csv(OUT_DIR / "fire_region_summary.csv", summary_rows)
    write_csv(OUT_DIR / "fire_correlations.csv", correlation_rows)
    plot_maps(
        lon,
        lat,
        np.where(land, gpp, np.nan),
        np.where(land, fire, np.nan),
        OUT_DIR / "gpp_fire_maps.png",
    )
    plot_scatter(gpp, fire, group_masks, OUT_DIR / "gpp_fire_scatter.png")

    metadata = {
        "history_file": str(NC_PATH),
        "fire_variable": "COL_FIRE_CLOSS",
        "fire_long_name": str(ds["COL_FIRE_CLOSS"].attrs.get("long_name", "")),
        "fire_units_source": str(ds["COL_FIRE_CLOSS"].attrs.get("units", "")),
        "conversion": "GPP and COL_FIRE_CLOSS multiplied by 365*86400 to annualize the 7300-day mean",
        "ring_width_degrees": RING_WIDTH_DEGREES,
        "valid_land_fire_min_gC_m2_yr": float(np.nanmin(fire[land])),
        "valid_land_fire_max_gC_m2_yr": float(np.nanmax(fire[land])),
        "valid_land_fire_nonzero_cell_share": float(np.count_nonzero(fire[land] > 0) / np.count_nonzero(land)),
        "boxes": BOXES,
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    ds.close()
    for path in sorted(OUT_DIR.iterdir()):
        print(path)


if __name__ == "__main__":
    main()
