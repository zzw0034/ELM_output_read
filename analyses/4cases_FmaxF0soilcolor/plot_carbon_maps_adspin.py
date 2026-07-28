"""
Quick-look carbon maps for a single ELM ad-spinup run.

Takes the path to an ad-spinup ELM history file (e.g.
20260619_Southeast_hires_s8_case1_soilcolor_ICB1850CNRDCTCBC_ad_spinup.elm.h0.0021-01-01-00000.nc)
and plots GPP, NEE, TOTVEGC, TOTSOMC as PNG + GeoTIFF, written to:

    outputs/<run_name>/

where <run_name> is the input file's basename without the .nc extension.

Notes
-----
- The averaging period is auto-detected from time_bounds via
  ``elmtools.process.detect_flux_scale_from_bounds`` (ad-spinup is yearly →
  gC/m²/year).

Usage:
    python plot_carbon_maps_adspin.py /path/to/*_ad_spinup.elm.h0.*.nc
"""

import os
import sys
import argparse

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
# from elmtools
from elmtools.process import detect_flux_scale_from_bounds
from elmtools.plot import plot_2d_map, save_geotiff

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR    = os.path.join(SCRIPT_DIR, "outputs")

# ── Variables ────────────────────────────────────────────────────────────────
# kind: "flux" → scaled by detect_flux_scale_from_bounds (yearly or monthly)
#       "pool" → use as-is (gC/m²)
VARIABLES = [
    {"name": "GPP",     "kind": "flux", "cmap": "YlGn",   "label": "GPP"},
    {"name": "NEE",     "kind": "flux", "cmap": "RdBu_r", "label": "NEE"},
    {"name": "TOTVEGC", "kind": "pool", "cmap": "Greens", "label": "Biomass (TOTVEGC)", "units": "gC/m²"},
    {"name": "TOTSOMC", "kind": "pool", "cmap": "YlOrBr", "label": "Soil C (TOTSOMC)",  "units": "gC/m²"},
]


# ── Process one run ──────────────────────────────────────────────────────────
def process_run(nc_path):
    if not os.path.isfile(nc_path):
        print(f"  ERROR: not found — {nc_path}")
        return

    run_name = os.path.splitext(os.path.basename(nc_path))[0]
    out_sub  = os.path.join(OUT_DIR, run_name)
    os.makedirs(out_sub, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"  Run:  {run_name}")
    print(f"  File: {nc_path}")
    print("=" * 70)

    ds = xr.open_dataset(nc_path, decode_times=True)
    lon = ds["lon"].values
    lat = ds["lat"].values
    extent_text = (
        f"extent: lon [{lon.min():.2f}, {lon.max():.2f}],  "
        f"lat [{lat.min():.2f}, {lat.max():.2f}]"
    )
    print(f"  lat: {lat.min():.4f}–{lat.max():.4f}  ({len(lat)} cells)")
    print(f"  lon: {lon.min():.4f}–{lon.max():.4f}  ({len(lon)} cells)")
    try:
        print(f"  time[0]: {ds['time'].values[0]}")
    except Exception:
        pass

    title_top = run_name

    # from elmtools
    flux_scale, flux_units = detect_flux_scale_from_bounds(ds)
    print(f"  flux scaling: × {flux_scale:.0f} s  →  {flux_units}")

    for cfg in VARIABLES:
        vname = cfg["name"]
        if vname not in ds:
            print(f"  skip {vname}: not in dataset")
            continue

        raw = ds[vname].isel(time=0).values
        if cfg["kind"] == "flux":
            data2d = raw * flux_scale
            units  = flux_units
        else:
            data2d = raw.astype(float)
            units  = cfg["units"]

        print(f"  {vname:8s} [{units}]  min={np.nanmin(data2d):10.2f}  "
              f"max={np.nanmax(data2d):10.2f}  mean={np.nanmean(data2d):10.2f}")

        png_path = os.path.join(out_sub, f"{vname}.png")
        tif_path = os.path.join(out_sub, f"{vname}.tif")

        # from elmtools
        plot_2d_map(
            data2d, lat, lon,
            var_name=cfg["label"],
            title=f"{cfg['label']} — {title_top}\n{extent_text}",
            outfile=png_path,
            cmap=cfg["cmap"],
            figsize=(10, 6),
            units=units,
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
        )
        # from elmtools
        save_geotiff(lon, lat, data2d, tif_path)

    ds.close()
    print(f"  → wrote PNG + TIFF to {out_sub}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Plot quick-look carbon maps for an ELM ad-spinup history file."
    )
    parser.add_argument("nc_path", help="Path to the ad-spinup ELM history NC file")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    process_run(args.nc_path)
    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
