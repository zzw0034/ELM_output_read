"""
Overlay domain-mean forest/crop/grass land-cover fraction (PCT_NAT_PFT x
PCT_LANDUNIT, from extract_landcover_fraction.py) against TOTVEGC_ABG (from
extract_annual_timeseries.py), to check whether the aboveground-biomass dip
(bottoming out 1957) is actually explained by the LUH2-driven forest ->
cropland transition, as hypothesized.

Run **locally**:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_landcover_vs_biomass_local.py
"""

import os

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CASE = "20260901_seus_halfdeg_transient"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

NC_LANDCOVER = os.path.join(OUT_DIR, "landcover_fraction.nc")
NC_TIMESERIES = os.path.join(OUT_DIR, "annual_timeseries.nc")


def main():
    lc = xr.open_dataset(NC_LANDCOVER)
    ts = xr.open_dataset(NC_TIMESERIES)
    years = lc["year"].values

    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)

    ax = axes[0]
    ax.plot(years, lc["forest_frac"].values, color="darkgreen", linewidth=1.5, label="Forest (tree PFTs)")
    ax.plot(years, lc["crop_total_frac"].values, color="goldenrod", linewidth=1.5, label="Cropland (generic crop PFT)")
    ax.plot(years, lc["grass_frac"].values, color="yellowgreen", linewidth=1.2, label="Grass")
    ax.plot(years, lc["shrub_frac"].values, color="sienna", linewidth=1.0, label="Shrub")
    ax.set_ylabel("% of gridcell\nland area")
    ax.legend(fontsize=8, loc="center left")
    ax.grid(True, alpha=0.3)
    ax.set_title(f"{CASE}: land-cover fraction vs. aboveground biomass")

    ax = axes[1]
    ax.plot(years, ts["TOTVEGC_ABG"].values, color="peru", linewidth=1.5)
    ax.set_ylabel("TOTVEGC_ABG\n(gC/m$^2$)")
    ax.grid(True, alpha=0.3)
    yr_min = int(ts["year"].values[np.nanargmin(ts["TOTVEGC_ABG"].values)])
    ax.axvline(yr_min, color="gray", linestyle="--", linewidth=0.8)
    ax.text(yr_min + 2, ts["TOTVEGC_ABG"].values.min(), f"min: {yr_min}", fontsize=8, color="gray")

    ax = axes[2]
    ax.plot(years, lc["forest_frac"].values, color="darkgreen", linewidth=1.5)
    ax.set_ylabel("Forest fraction\n(%, zoomed)")
    ax.set_xlabel("Year")
    ax.grid(True, alpha=0.3)
    yr_min_forest = int(years[np.nanargmin(lc["forest_frac"].values)])
    ax.axvline(yr_min_forest, color="gray", linestyle="--", linewidth=0.8)
    ax.text(yr_min_forest + 2, lc["forest_frac"].values.min(), f"min: {yr_min_forest}", fontsize=8, color="gray")

    fig.tight_layout()
    out_path = os.path.join(OUT_DIR, "landcover_vs_biomass.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")

    print(f"\nForest fraction minimum year: {yr_min_forest} ({lc['forest_frac'].values.min():.2f}%, "
          f"vs {lc['forest_frac'].values[0]:.2f}% in 1850)")
    print(f"TOTVEGC_ABG minimum year: {yr_min} ({ts['TOTVEGC_ABG'].values.min():.1f} gC/m^2)")
    print(f"Forest fraction 2023: {lc['forest_frac'].values[-1]:.2f}% "
          f"({'recovered close to' if lc['forest_frac'].values[-1] > 0.9*lc['forest_frac'].values[0] else 'still well below'} 1850 level)")


if __name__ == "__main__":
    main()
