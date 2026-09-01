"""
Extended QC diagnostics for 20260901_seus_halfdeg_transient, from
extract_annual_timeseries.py's output (outputs/annual_timeseries.nc).

Three figures, following up on the TOTVEGC vs TOTVEGC_ABG divergence flagged
from the first look at this run, and the suggested variable list that came
out of it:

  1. biomass_breakdown_disturbance.png
     TOTVEGC / TOTVEGC_ABG / TOTVEGC_BLG together, with WOOD_HARVESTC and
     fire (PFT_FIRE_CLOSS, FAREA_BURNED) stacked below on the same time
     axis -- lines up *when* aboveground biomass drops against *when*
     harvest/fire disturbance happens, rather than just noting they both
     move.
  2. water_energy_balance.png
     RAIN/SNOW/QRUNOFF and EFLX_LH_TOT/FSH -- a basic closure sanity check
     (does runoff track precipitation, does the seasonal-mean energy
     partition look physical) that all downstream carbon numbers implicitly
     depend on.
  3. n_cycle_diagnostics.png
     SMINN, NDEP_TO_SMINN, SUPPLEMENT_TO_SMINN -- SUPPLEMENT_TO_SMINN should
     stay at (or very near) 0; a sustained nonzero value would mean the
     model is leaning on non-mechanistic N supply rather than the real N
     cycle to sustain the productivity increase seen in GPP/NPP.

Run **locally** after pulling outputs/annual_timeseries.nc back from
Pathfinder:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_diagnostics_local.py
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


def savefig(fig, name):
    out_path = os.path.join(OUT_DIR, name)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def figure_biomass_breakdown_disturbance(ds, years):
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True,
                              gridspec_kw={"height_ratios": [2, 1, 1]})

    ax = axes[0]
    ax.plot(years, ds["TOTVEGC"].values, label="TOTVEGC (total)", color="black", linewidth=1.5)
    ax.plot(years, ds["TOTVEGC_ABG"].values, label="TOTVEGC_ABG (aboveground)", color="peru")
    ax.plot(years, ds["TOTVEGC_BLG"].values, label="TOTVEGC_BLG (belowground = total-ABG)", color="darkgreen")
    ax.set_ylabel("Vegetation C (gC/m$^2$)")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_title(f"{CASE}: biomass breakdown vs. disturbance (domain-mean, area*landfrac-weighted)")

    ax = axes[1]
    ax.plot(years, ds["WOOD_HARVESTC"].values, color="saddlebrown")
    ax.set_ylabel("WOOD_HARVESTC\n(gC/m$^2$/yr)")
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    ax.plot(years, ds["PFT_FIRE_CLOSS"].values, color="firebrick", label="PFT_FIRE_CLOSS (gC/m$^2$/yr)")
    ax.set_ylabel("PFT_FIRE_CLOSS\n(gC/m$^2$/yr)", color="firebrick")
    ax.tick_params(axis="y", labelcolor="firebrick")
    ax2 = ax.twinx()
    ax2.plot(years, ds["FAREA_BURNED"].values, color="darkorange", linestyle="--", label="FAREA_BURNED")
    ax2.set_ylabel("FAREA_BURNED\n(fraction/yr, approx)", color="darkorange")
    ax2.tick_params(axis="y", labelcolor="darkorange")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Year")

    fig.tight_layout()
    savefig(fig, "biomass_breakdown_disturbance.png")


def figure_water_energy_balance(ds, years):
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

    ax = axes[0]
    ax.plot(years, ds["RAIN"].values, label="RAIN", color="steelblue")
    ax.plot(years, ds["SNOW"].values, label="SNOW", color="lightblue")
    ax.plot(years, ds["QRUNOFF"].values, label="QRUNOFF", color="teal")
    ax.set_ylabel("mm/yr")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_title(f"{CASE}: water and energy balance (domain-mean, area*landfrac-weighted)")

    ax = axes[1]
    ax.plot(years, ds["EFLX_LH_TOT"].values, label="EFLX_LH_TOT (latent heat)", color="crimson")
    ax.plot(years, ds["FSH"].values, label="FSH (sensible heat)", color="darkorange")
    ax.set_ylabel("W/m$^2$ (annual mean)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Year")

    fig.tight_layout()
    savefig(fig, "water_energy_balance.png")


def figure_n_cycle(ds, years):
    fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)

    ax = axes[0]
    ax.plot(years, ds["SMINN"].values, color="mediumpurple")
    ax.set_ylabel("SMINN\n(gN/m$^2$)")
    ax.grid(True, alpha=0.3)
    ax.set_title(f"{CASE}: N-cycle diagnostics (domain-mean, area*landfrac-weighted)")

    ax = axes[1]
    ax.plot(years, ds["NDEP_TO_SMINN"].values, color="steelblue")
    ax.set_ylabel("NDEP_TO_SMINN\n(gN/m$^2$/yr)")
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    supp = ds["SUPPLEMENT_TO_SMINN"].values
    ax.plot(years, supp, color="crimson")
    ax.set_ylabel("SUPPLEMENT_TO_SMINN\n(gN/m$^2$/yr)")
    ax.set_xlabel("Year")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.01, max(0.01, float(np.nanmax(supp)) * 1.5))
    ax.text(0.02, 0.85, f"max={np.nanmax(supp):.3g}, should stay ~0",
            transform=ax.transAxes, fontsize=8, color="crimson")

    fig.tight_layout()
    savefig(fig, "n_cycle_diagnostics.png")


def main():
    ds = xr.open_dataset(NC_PATH)
    years = ds["year"].values

    figure_biomass_breakdown_disturbance(ds, years)
    figure_water_energy_balance(ds, years)
    figure_n_cycle(ds, years)

    print("\nWhere is peak fire / harvest?")
    yr_max_fire = years[np.nanargmax(ds["PFT_FIRE_CLOSS"].values)]
    yr_max_burn = years[np.nanargmax(ds["FAREA_BURNED"].values)]
    yr_max_harv = years[np.nanargmax(ds["WOOD_HARVESTC"].values)]
    yr_min_abg = years[np.nanargmin(ds["TOTVEGC_ABG"].values)]
    print(f"  PFT_FIRE_CLOSS peak:  {yr_max_fire}  (value={float(ds['PFT_FIRE_CLOSS'].max()):.3g})")
    print(f"  FAREA_BURNED peak:    {yr_max_burn}  (value={float(ds['FAREA_BURNED'].max()):.3g})")
    print(f"  WOOD_HARVESTC peak:   {yr_max_harv}  (value={float(ds['WOOD_HARVESTC'].max()):.3g})")
    print(f"  TOTVEGC_ABG minimum:  {yr_min_abg}  (value={float(ds['TOTVEGC_ABG'].min()):.3g})")


if __name__ == "__main__":
    main()
