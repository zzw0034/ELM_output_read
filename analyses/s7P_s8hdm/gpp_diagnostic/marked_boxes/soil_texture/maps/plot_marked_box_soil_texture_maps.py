#!/usr/bin/env python
"""Plot soil-texture maps with the two diagnosed GPP boxes overlaid."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import xarray as xr


NC_PATH = Path(os.environ["NC_PATH"])
SURFDATA_PATH = Path(os.environ["SURFDATA_PATH"])
OUT_DIR = Path(os.environ["OUT_DIR"])
FILL_LIMIT = 1.0e30

BOXES = {
    "Upper box": {"lon_min": -85.5, "lon_max": -82.2, "lat_min": 30.7, "lat_max": 32.9},
    "Lower box": {"lon_min": -86.3, "lon_max": -80.4, "lat_min": 27.5, "lat_max": 30.5},
}


def clean(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    result[~np.isfinite(result) | (np.abs(result) >= FILL_LIMIT)] = np.nan
    return result


def add_boxes(axis: plt.Axes) -> None:
    for label, bounds in BOXES.items():
        rectangle = Rectangle(
            (bounds["lon_min"], bounds["lat_min"]),
            bounds["lon_max"] - bounds["lon_min"],
            bounds["lat_max"] - bounds["lat_min"],
            fill=False,
            edgecolor="#d62728",
            linewidth=1.5,
            zorder=5,
        )
        axis.add_patch(rectangle)
        axis.text(
            bounds["lon_min"] + 0.08,
            bounds["lat_max"] + 0.08,
            label,
            color="#b11f24",
            fontsize=8,
            weight="bold",
            zorder=6,
        )


def configure_axis(axis: plt.Axes, lon: np.ndarray, lat: np.ndarray) -> None:
    axis.set_xlim(float(np.nanmin(lon)), float(np.nanmax(lon)))
    axis.set_ylim(float(np.nanmin(lat)), float(np.nanmax(lat)))
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.grid(color="0.85", linewidth=0.35, alpha=0.6)
    add_boxes(axis)


def plot_texture_layer(
    lon: np.ndarray,
    lat: np.ndarray,
    sand: np.ndarray,
    clay: np.ndarray,
    layer: int,
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(15, 6.2), constrained_layout=True)
    panels = (
        (axes[0], sand, "Sand fraction", "YlOrBr"),
        (axes[1], clay, "Clay fraction", "PuRd"),
    )
    for axis, values, title, cmap in panels:
        mesh = axis.pcolormesh(lon, lat, values, shading="auto", cmap=cmap, vmin=0, vmax=100)
        configure_axis(axis, lon, lat)
        axis.set_title(f"{title} — soil layer {layer}")
        colorbar = figure.colorbar(mesh, ax=axis, shrink=0.88, pad=0.02)
        colorbar.set_label("Percent (%)")
    figure.suptitle("ELM surface soil texture with marked low-GPP boxes", fontsize=15)
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def plot_organic_layer(
    lon: np.ndarray,
    lat: np.ndarray,
    organic: np.ndarray,
    layer: int,
    output_path: Path,
) -> None:
    valid = organic[np.isfinite(organic)]
    vmax = float(np.nanquantile(valid, 0.98))
    figure, axis = plt.subplots(figsize=(10.8, 7.0), constrained_layout=True)
    mesh = axis.pcolormesh(lon, lat, organic, shading="auto", cmap="YlGn", vmin=0, vmax=vmax)
    configure_axis(axis, lon, lat)
    axis.set_title(f"Organic matter density — soil layer {layer}")
    colorbar = figure.colorbar(mesh, ax=axis, shrink=0.9, pad=0.02, extend="max")
    colorbar.set_label("kg m⁻³")
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    history = xr.open_dataset(NC_PATH, decode_times=False)
    surf = xr.open_dataset(SURFDATA_PATH, decode_times=False)

    lon = clean(history["lon"].values)
    lat = clean(history["lat"].values)
    land = (
        (np.asarray(history["landmask"].values) == 1)
        & np.isfinite(history["landfrac"].values)
        & (history["landfrac"].values >= 0.5)
    )
    sand = clean(surf["PCT_SAND"].values)
    clay = clean(surf["PCT_CLAY"].values)
    organic = clean(surf["ORGANIC"].values)

    for layer in (0, 7):
        plot_texture_layer(
            lon,
            lat,
            np.where(land, sand[layer], np.nan),
            np.where(land, clay[layer], np.nan),
            layer,
            OUT_DIR / f"soil_texture_layer{layer}.png",
        )
    plot_organic_layer(
        lon,
        lat,
        np.where(land, organic[2], np.nan),
        2,
        OUT_DIR / "soil_organic_layer2.png",
    )

    history.close()
    surf.close()
    for path in sorted(OUT_DIR.glob("*.png")):
        print(path)


if __name__ == "__main__":
    main()
