"""
Quick-look urban fraction and natural-PFT fraction maps from an ELM surface
dataset (surfdata.nc).

Plots:
    - Total urban fraction (sum of PCT_URBAN over density classes)
    - Fraction of each natural PFT (PCT_NAT_PFT) that is non-zero anywhere
      in the domain

as PNG + GeoTIFF, written to:

    outputs/surfdata/

Usage:
    python plot_urban_pft_maps.py /path/to/surfdata.nc
"""

import os
import sys
import argparse

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
# from elmtools
from elmtools.plot import plot_2d_map, save_geotiff

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR    = os.path.join(SCRIPT_DIR, "outputs")

# CLM5/ELM standard natural-PFT names (natpft index 0-16)
NATPFT_NAMES = [
    "0_bare_soil",
    "1_needleleaf_evergreen_temperate_tree",
    "2_needleleaf_evergreen_boreal_tree",
    "3_needleleaf_deciduous_boreal_tree",
    "4_broadleaf_evergreen_tropical_tree",
    "5_broadleaf_evergreen_temperate_tree",
    "6_broadleaf_deciduous_tropical_tree",
    "7_broadleaf_deciduous_temperate_tree",
    "8_broadleaf_deciduous_boreal_tree",
    "9_broadleaf_evergreen_shrub",
    "10_broadleaf_deciduous_temperate_shrub",
    "11_broadleaf_deciduous_boreal_shrub",
    "12_c3_arctic_grass",
    "13_c3_non-arctic_grass",
    "14_c4_grass",
    "15_c3_crop",
    "16_c3_irrigated_crop",
]


def process(surfdata_path):
    if not os.path.isfile(surfdata_path):
        print(f"  ERROR: not found — {surfdata_path}")
        return

    run_name = "surfdata"
    out_sub  = os.path.join(OUT_DIR, run_name)
    os.makedirs(out_sub, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"  Surface dataset: {surfdata_path}")
    print("=" * 70)

    ds = xr.open_dataset(surfdata_path, decode_times=False)
    lat = ds["LATIXY"].values[:, 0]
    lon = ds["LONGXY"].values[0, :]
    extent_text = (
        f"extent: lon [{lon.min():.2f}, {lon.max():.2f}],  "
        f"lat [{lat.min():.2f}, {lat.max():.2f}]"
    )
    print(f"  lat: {lat.min():.4f}–{lat.max():.4f}  ({len(lat)} cells)")
    print(f"  lon: {lon.min():.4f}–{lon.max():.4f}  ({len(lon)} cells)")

    # ── Urban fraction (sum of the 3 density classes) ──────────────────────
    urban_pct = ds["PCT_URBAN"].sum(dim="numurbl").values.astype(float)
    print(f"  Urban fraction [%]  min={np.nanmin(urban_pct):8.3f}  "
          f"max={np.nanmax(urban_pct):8.3f}  mean={np.nanmean(urban_pct):8.3f}")

    png_path = os.path.join(out_sub, "PCT_URBAN_total.png")
    tif_path = os.path.join(out_sub, "PCT_URBAN_total.tif")
    plot_2d_map(
        urban_pct, lat, lon,
        var_name="Total Urban Fraction",
        title=f"Total Urban Fraction — {run_name}\n{extent_text}",
        outfile=png_path,
        cmap="Reds",
        figsize=(10, 6),
        units="%",
        add_coastlines=True,
        add_states=True,
        add_borders=True,
        add_gridlines=True,
        set_extent=True,
    )
    save_geotiff(lon, lat, urban_pct, tif_path)

    # ── PFT fraction: one map per natural PFT that is present in the domain ─
    pft = ds["PCT_NAT_PFT"]
    n_pft = pft.sizes["natpft"]
    for i in range(n_pft):
        data2d = pft.isel(natpft=i).values.astype(float)
        vmax = np.nanmax(data2d)
        if vmax <= 0:
            print(f"  skip natpft {i}: all zero in domain")
            continue

        name = NATPFT_NAMES[i] if i < len(NATPFT_NAMES) else f"{i}_unknown"
        print(f"  PFT {name:45s} [%]  min={np.nanmin(data2d):8.3f}  "
              f"max={vmax:8.3f}  mean={np.nanmean(data2d):8.3f}")

        png_path = os.path.join(out_sub, f"PCT_NAT_PFT_{name}.png")
        tif_path = os.path.join(out_sub, f"PCT_NAT_PFT_{name}.tif")
        plot_2d_map(
            data2d, lat, lon,
            var_name=f"PFT Fraction ({name})",
            title=f"PFT Fraction — {name}\n{run_name}\n{extent_text}",
            outfile=png_path,
            cmap="Greens",
            figsize=(10, 6),
            units="%",
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
        )
        save_geotiff(lon, lat, data2d, tif_path)

    ds.close()
    print(f"  → wrote PNG + TIFF to {out_sub}")


def main():
    parser = argparse.ArgumentParser(
        description="Plot urban fraction and natural-PFT fraction maps from surfdata.nc."
    )
    parser.add_argument("surfdata_path", help="Path to surfdata.nc")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    process(args.surfdata_path)
    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
