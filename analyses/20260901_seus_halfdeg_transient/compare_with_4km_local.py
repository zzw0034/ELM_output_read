"""
Overlay the 0.5 deg run's (20260901_seus_halfdeg_transient) domain-mean GPP,
TOTVEGC, and SOC 0-30cm annual time series against the 4 km reference case
(20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC), to check
the two resolutions converge to similar magnitudes and trends -- the most
direct QC available for a downscaling exercise.

Reads:
  - outputs/annual_timeseries.nc (this folder; the 0.5 deg run)
  - ../20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC/
    outputs/annual_timeseries_full.nc (the 4 km reference)

Run **locally**:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python compare_with_4km_local.py
"""

import os

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

NC_05DEG = os.path.join(OUT_DIR, "annual_timeseries.nc")
NC_4KM = os.path.join(
    SCRIPT_DIR, "..", "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC",
    "outputs", "annual_timeseries_full.nc",
)

PANELS = [
    ("GPP", "GPP", "gC/m$^2$/yr"),
    ("TOTVEGC", "Total vegetation C (biomass)", "gC/m$^2$"),
    ("SOC_0_30cm", "Soil organic C, 0-30 cm", "gC/m$^2$"),
]


def main():
    ds_05 = xr.open_dataset(NC_05DEG)
    ds_4km = xr.open_dataset(NC_4KM)

    fig, axes = plt.subplots(len(PANELS), 1, figsize=(9, 3.2 * len(PANELS)), sharex=True)
    for ax, (var, label, units) in zip(axes, PANELS):
        ax.plot(ds_4km["year"].values, ds_4km[var].values, color="black",
                 linewidth=1.3, label="4 km (20260723_..._harvfix)")
        ax.plot(ds_05["year"].values, ds_05[var].values, color="crimson",
                 linewidth=1.3, linestyle="--", label="0.5 deg (20260901_seus_halfdeg_transient)")
        ax.set_ylabel(f"{label}\n({units})")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
    axes[0].set_title("0.5 deg vs 4 km: domain-mean annual time series (both area*landfrac-weighted)")
    axes[-1].set_xlabel("Year")
    fig.tight_layout()

    out_path = os.path.join(OUT_DIR, "compare_with_4km.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")

    print("\nFirst5 / last5 year means, 0.5deg vs 4km, and % difference at each end:")
    for var, label, units in PANELS:
        v05 = ds_05[var].values
        v4k = ds_4km[var].values
        f05, l05 = v05[:5].mean(), v05[-5:].mean()
        f4k, l4k = v4k[:5].mean(), v4k[-5:].mean()
        print(f"  {label:28s} first5: 0.5deg={f05:9.3g} 4km={f4k:9.3g} diff={100*(f05-f4k)/f4k:+6.1f}%   "
              f"last5: 0.5deg={l05:9.3g} 4km={l4k:9.3g} diff={100*(l05-l4k)/l4k:+6.1f}%   ({units})")


if __name__ == "__main__":
    main()
