"""
Plot domain-mean annual time series (GPP, biomass, soil C 0-30cm, plus
TOTSOMC_1m and NDEP for context) for the 0.5 deg SEUS transient run
(20260901_seus_halfdeg_transient), from extract_annual_timeseries.py's
output.

Run **locally** after pulling outputs/annual_timeseries.nc back from
Pathfinder:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_annual_timeseries_local.py
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
NC_PATH = os.path.join(OUT_DIR, "annual_timeseries.nc")

PANELS = [
    ("GPP", "GPP", "gC/m$^2$/yr", "seagreen"),
    ("TOTVEGC", "Total vegetation C (biomass)", "gC/m$^2$", "peru"),
    ("SOC_0_30cm", "Soil organic C, 0-30 cm", "gC/m$^2$", "sienna"),
    ("TOTSOMC_1m", "Soil organic C, 0-100 cm (for reference)", "gC/m$^2$", "saddlebrown"),
    ("NDEP_TO_SMINN", "Atmospheric N deposition", "gN/m$^2$/yr", "steelblue"),
]


def main():
    ds = xr.open_dataset(NC_PATH)
    years = ds["year"].values

    fig, axes = plt.subplots(len(PANELS), 1, figsize=(9, 3 * len(PANELS)), sharex=True)
    for ax, (var, label, units, color) in zip(axes, PANELS):
        vals = ds[var].values
        ax.plot(years, vals, color=color, linewidth=1.3)
        ax.set_ylabel(f"{label}\n({units})")
        ax.grid(True, alpha=0.3)
        ax.axvline(2005, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    axes[0].set_title(f"{CASE}: domain-mean annual time series (area*landfrac-weighted)")
    axes[-1].set_xlabel("Year")
    fig.tight_layout()

    out_path = os.path.join(OUT_DIR, "annual_timeseries.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")

    print("\nSummary (first / last 5 years):")
    for var, label, units, _ in PANELS:
        vals = ds[var].values
        print(f"  {label:45s} {vals[:5].mean():10.3g} -> {vals[-5:].mean():10.3g} {units}")


if __name__ == "__main__":
    main()
