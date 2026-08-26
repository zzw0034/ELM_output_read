"""
High-res "showcase" carbon maps for the completed SEUS historical run
20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC (1850-2023,
LUH2-harvest-downscaling fix + human-population-density fix applied — the
only Southeast-hires case that ran to completion).

Produces four maps for a "best high-res capability" slide:
  - GPP, 2014-2023 10-year mean annual total     [gC/m^2/year]
  - NPP, 2014-2023 10-year mean annual total     [gC/m^2/year]
  - Soil organic C, 0-30 cm, end-of-run (Dec 2023) snapshot   [kgC/m^2]
  - Soil organic C, full profile, end-of-run (Dec 2023) snapshot  [kgC/m^2]

Time labeling
-------------
Each h0 file <case>.elm.h0.<Y>-02-01-00000.nc holds 12 monthly records
raw-stamped Y-02-01 .. (Y+1)-01-01 (ELM stamps a monthly mean on the 1st of
the *following* month). Every stamp is shifted back one month with
elmtools.process.subtract_month_cftime *before* computing days-in-month, so
January's rate is weighted by January's 31 days rather than February's 28,
etc. (flux_to_monthly() would get this wrong if called on the raw stamps.)

Soil depths
-----------
SOIL1C_vr..SOIL4C_vr are carbon *density* (gC/m^3) on levdcmp layers. Layer
thickness (DZSOI) is written only once, in the case's first (1850) h0 file,
as ELM's "Time_constant_3Dvars". The 0-30 cm integral uses the exact
per-layer overlap with the [0, 0.3 m] interval from DZSOI's own cumulative
depth (layers 1-5 fully included, layer 6 partially — verified against this
run's actual layer thicknesses), so it does not depend on assuming a fixed
number of layers. The full-profile panel uses TOTSOMC as-is (the model's own
full-column integral).

Usage
-----
    python plot_gpp_npp_soilc_maps.py
"""

import os
import sys

import numpy as np
import xarray as xr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files, open_elm_dataset
from elmtools.process import (
    flux_to_monthly,
    aggregate_monthly_to_yearly,
    subtract_month_cftime,
)
from elmtools.plot import plot_2d_map, save_geotiff

# ── Paths ─────────────────────────────────────────────────────────────────
CASE = "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC"
RUN_DIR = f"/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/{CASE}/run"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")

YEAR_MIN, YEAR_MAX = 2014, 2023
TARGET_DEPTH_M = 0.30

SOIL_POOL_VARS = ["SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]


# ── Helpers ──────────────────────────────────────────────────────────────

def shift_time_back_one_month(ds: xr.Dataset) -> xr.Dataset:
    """Relabel h0 records from 'stamped on 1st of following month' to the
    true month the average covers (see module docstring)."""
    corrected = np.array([subtract_month_cftime(t) for t in ds["time"].values])
    return ds.assign_coords(time=corrected)


def annual_total_flux_map(ds: xr.Dataset, var: str) -> xr.DataArray:
    """gC/m^2/s monthly records -> per-calendar-year gC/m^2/year totals,
    dims (year, lat, lon)."""
    da = shift_time_back_one_month(ds)[var]
    monthly_total = flux_to_monthly(da)              # gC/m^2/month, correct day-counts
    yearly_total = aggregate_monthly_to_yearly(       # gC/m^2/year
        monthly_total, method="sum", time_offset=False  # already shifted above
    )
    return yearly_total


def soilc_0_30cm(ds_last: xr.Dataset, dzsoi: xr.DataArray) -> np.ndarray:
    """Integrate SOIL1-4C_vr (gC/m^3) over the 0-0.30 m interval using each
    layer's exact overlap with that interval, from DZSOI's cumulative depth.
    Returns a (lat, lon) array in gC/m^2."""
    total_vr = sum(ds_last[v] for v in SOIL_POOL_VARS)  # (levdcmp, lat, lon), gC/m^3

    dz = dzsoi.values                                    # (levgrnd, lat, lon), m
    layer_bottom = np.cumsum(dz, axis=0)
    layer_top = layer_bottom - dz
    overlap = np.clip(np.minimum(layer_bottom, TARGET_DEPTH_M) - layer_top, 0.0, None)

    contrib = total_vr.values * overlap                  # gC/m^2 per layer
    return np.nansum(contrib, axis=0)


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    files = find_h0_files(RUN_DIR, year_min=YEAR_MIN, year_max=YEAR_MAX)
    print(f"Found {len(files)} h0 files for {YEAR_MIN}-{YEAR_MAX}:")
    for f in files:
        print(" ", os.path.basename(f))
    assert len(files) == YEAR_MAX - YEAR_MIN + 1, "expected one h0 file per year"

    # ---- GPP / NPP: 10-year mean annual total ----------------------------
    ds_flux = open_elm_dataset(files, vars_to_read=["GPP", "NPP"])
    lat = ds_flux["lat"].values
    lon = ds_flux["lon"].values

    gpp_yearly = annual_total_flux_map(ds_flux, "GPP")
    npp_yearly = annual_total_flux_map(ds_flux, "NPP")
    print(f"  GPP yearly totals cover years: {gpp_yearly['year'].values.tolist()}")

    gpp_10yr = gpp_yearly.mean(dim="year", skipna=True).values
    npp_10yr = npp_yearly.mean(dim="year", skipna=True).values
    ds_flux.close()

    # ---- Soil C: end-of-run (Dec 2023) snapshot ---------------------------
    last_file = files[-1]  # 2023-02-01 file: records true Jan-Dec 2023 after shift
    ds_soil = xr.open_dataset(last_file, decode_times=True)
    ds_soil_shifted = shift_time_back_one_month(ds_soil)
    true_months = [t.month for t in ds_soil_shifted["time"].values]
    dec_idx = true_months.index(12)
    dec2023 = ds_soil_shifted.isel(time=dec_idx)

    totsomc_full_gC = dec2023["TOTSOMC"].values           # gC/m^2, model's own full-profile integral
    soilc_full_kgC = totsomc_full_gC / 1000.0

    first_file = find_h0_files(RUN_DIR, year_min=1850, year_max=1850)[0]
    ds_static = xr.open_dataset(first_file, decode_times=True)
    dzsoi = ds_static["DZSOI"]                             # (levgrnd, lat, lon), m
    soilc_030_gC = soilc_0_30cm(dec2023, dzsoi)
    soilc_030_kgC = soilc_030_gC / 1000.0
    ds_static.close()

    # mask non-land with landmask from the soil dataset
    landmask = ds_soil["landmask"].values if "landmask" in ds_soil else None
    if landmask is not None:
        land_nan = np.where(landmask == 1, 1.0, np.nan)
        soilc_full_kgC = soilc_full_kgC * land_nan
        soilc_030_kgC = soilc_030_kgC * land_nan
    ds_soil.close()

    # ---- Report + plot ------------------------------------------------
    panels = [
        {
            "data": gpp_10yr, "var": "GPP", "label": "GPP",
            "title": f"GPP — {YEAR_MIN}-{YEAR_MAX} mean annual total\n{CASE}",
            "units": "gC/m^2/year", "cmap": "YlGn",
            "fname": f"GPP_{YEAR_MIN}-{YEAR_MAX}mean",
        },
        {
            "data": npp_10yr, "var": "NPP", "label": "NPP",
            "title": f"NPP — {YEAR_MIN}-{YEAR_MAX} mean annual total\n{CASE}",
            "units": "gC/m^2/year", "cmap": "YlGn",
            "fname": f"NPP_{YEAR_MIN}-{YEAR_MAX}mean",
        },
        {
            "data": soilc_030_kgC, "var": "SoilC_0-30cm", "label": "Soil organic C (0-30 cm)",
            "title": f"Soil organic C, 0-30 cm — end of run (Dec 2023)\n{CASE}",
            "units": "kgC/m^2", "cmap": "YlOrBr",
            "fname": "SoilC_0-30cm_2023",
        },
        {
            "data": soilc_full_kgC, "var": "SoilC_fullprofile", "label": "Soil organic C (full profile)",
            "title": f"Soil organic C, full profile — end of run (Dec 2023)\n{CASE}",
            "units": "kgC/m^2", "cmap": "YlOrBr",
            "fname": "SoilC_fullprofile_2023",
        },
    ]

    for p in panels:
        d = p["data"]
        print(f"  {p['var']:20s} [{p['units']}]  "
              f"min={np.nanmin(d):10.3f}  max={np.nanmax(d):10.3f}  mean={np.nanmean(d):10.3f}")

        png_path = os.path.join(OUT_DIR, f"{p['fname']}.png")
        tif_path = os.path.join(OUT_DIR, f"{p['fname']}.tif")
        plot_2d_map(
            d, lat, lon,
            var_name=p["label"],
            title=p["title"],
            outfile=png_path,
            cmap=p["cmap"],
            figsize=(10, 6),
            units=p["units"],
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
        )
        save_geotiff(lon, lat, d, tif_path)

    print(f"\nDone. Outputs under: {OUT_DIR}")


if __name__ == "__main__":
    main()
