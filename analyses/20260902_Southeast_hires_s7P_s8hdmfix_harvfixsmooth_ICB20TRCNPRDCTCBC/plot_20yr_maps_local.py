"""
Re-plot the every-20-years snapshot maps with US state boundaries, from the
GeoTIFFs written on Pathfinder by extract_20yr_maps.py and rsync'd back.

Runs **locally** (the Pathfinder conda env has no cartopy):
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_20yr_maps_local.py

Color scales
------------
Two versions are written for every variable:

  <Var>_<year>.png           one shared quantile color scale, built from all
                             years pooled -- panels are comparable across
                             years, so the series reads as an actual time
                             evolution.
  <Var>_selfscaled_<year>.png  per-year quantile scale, which is what the
                             20260723 figures used. Self-scaling stretches
                             whatever contrast a single year has, so it is
                             the strictest look at residual 0.25 deg block
                             structure -- and the like-for-like comparison
                             against the old run's Biomass_2010.png.

Both use equal-population (quantile) bins rather than a linear ramp, matching
the 20260723 convention.
"""

import os
import sys

import numpy as np
import rioxarray as rxr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.plot import plot_2d_map

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
YEARS = [1850, 1870, 1890, 1910, 1930, 1950, 1970, 1990, 2010, 2023]

# same brown-teal, white-dropped BrBG used for SOC in the 20260723 analysis
BRBG_NO_WHITE = LinearSegmentedColormap.from_list(
    "BrBG_no_white",
    [c for i, c in enumerate(plt.get_cmap("BrBG")(np.linspace(0, 1, 9))) if i != 4],
    N=256,
)

VARIABLES = [
    {
        "prefix": "Biomass", "label": "Aboveground biomass (TOTVEGC_ABG)",
        "title": "Aboveground biomass", "units": "kgC/m^2", "cmap": "viridis",
    },
    {
        "prefix": "AnnualHarvest", "label": "Annual wood harvest",
        "title": "Annual wood harvest (smoothed forcing)",
        "units": "unitless", "cmap": "OrRd",
    },
    {
        "prefix": "GPP", "label": "GPP", "title": "GPP annual total",
        "units": "gC/m^2/year", "cmap": "YlGn",
    },
    {
        "prefix": "NPP", "label": "NPP", "title": "NPP annual total",
        "units": "gC/m^2/year", "cmap": "YlGn",
    },
    {
        "prefix": "SoilC_0-30cm", "label": "Soil organic C (0-30 cm)",
        "title": "Soil organic C, 0-30 cm (Dec)", "units": "kgC/m^2",
        "cmap": BRBG_NO_WHITE,
    },
]


def read_tif(path: str):
    """Return (array with nodata as NaN, lat, lon)."""
    da = rxr.open_rasterio(path).squeeze("band", drop=True)
    arr = da.values.astype(float)
    nodata = da.rio.nodata
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr, da["y"].values, da["x"].values


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50):
    """Equal-population color bins. Returns None when the field is degenerate
    (all zero, or fewer than two distinct quantile edges), letting
    plot_2d_map auto-scale instead."""
    finite = data[np.isfinite(data)]
    if finite.size == 0 or finite.max() <= finite.min():
        return None
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    if len(edges) < 2:
        return None
    return BoundaryNorm(edges, ncolors=256)


def main():
    for spec in VARIABLES:
        prefix = spec["prefix"]
        paths = {yr: os.path.join(OUT_DIR, f"{prefix}_{yr}.tif") for yr in YEARS}
        available = {yr: p for yr, p in paths.items() if os.path.exists(p)}
        if not available:
            print(f"{prefix}: no GeoTIFFs found; skipping")
            continue

        fields = {}
        for yr, p in available.items():
            arr, lat, lon = read_tif(p)
            fields[yr] = (arr, lat, lon)

        pooled = np.concatenate([a[np.isfinite(a)].ravel() for a, _, _ in fields.values()])
        shared_norm = quantile_boundary_norm(pooled)

        for yr, (arr, lat, lon) in fields.items():
            print(f"  {prefix}_{yr}  min={np.nanmin(arr):.4f}  "
                  f"max={np.nanmax(arr):.4f}  mean={np.nanmean(arr):.4f}")
            plot_2d_map(
                arr, lat, lon,
                var_name=spec["label"],
                title=f"{spec['title']} — {yr}",
                outfile=os.path.join(OUT_DIR, f"{prefix}_{yr}.png"),
                cmap=spec["cmap"], norm=shared_norm, figsize=(10, 6),
                units=spec["units"],
                add_coastlines=True, add_states=True, add_borders=True,
                add_gridlines=True, set_extent=True, cbar_location="bottom",
            )
            plot_2d_map(
                arr, lat, lon,
                var_name=spec["label"],
                title=f"{spec['title']} — {yr} (self-scaled)",
                outfile=os.path.join(OUT_DIR, f"{prefix}_selfscaled_{yr}.png"),
                cmap=spec["cmap"], norm=quantile_boundary_norm(arr),
                figsize=(10, 6), units=spec["units"],
                add_coastlines=True, add_states=True, add_borders=True,
                add_gridlines=True, set_extent=True, cbar_location="bottom",
            )

    print(f"\nDone. Figures under: {OUT_DIR}")


if __name__ == "__main__":
    main()
