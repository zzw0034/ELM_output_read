"""
High-res "showcase" carbon maps for the completed SEUS historical run
20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC (1850-2023,
LUH2-harvest-downscaling fix + human-population-density fix applied — the
only Southeast-hires case that ran to completion).

Produces seven maps for a "best high-res capability" slide:
  - GPP, 2014-2023 10-year mean annual total     [gC/m^2/year]
  - NPP, 2014-2023 10-year mean annual total     [gC/m^2/year]
  - Aboveground biomass (TOTVEGC_ABG), 2014-2023 mean (same years as GPP/NPP) [kgC/m^2]
  - Aboveground biomass (TOTVEGC_ABG), 1850 (run's first year -- little
    accumulated harvest yet, so the 0.25 deg block pattern below should be
    much weaker than in the 2014-2023 panel)                [kgC/m^2]
  - Soil organic C, 0-30 cm, end-of-run (Dec 2023) snapshot   [kgC/m^2]
  - Soil organic C, 0-100 cm, end-of-run (Dec 2023) snapshot  [kgC/m^2]
  - Soil organic C, full profile, end-of-run (Dec 2023) snapshot  [kgC/m^2]

Biomass caveat
--------------
TOTVEGC_ABG is a pool that integrates decades of wood-harvest disturbance
history, and that history comes from LUH2 at native 0.25 deg resolution --
even after harvfix's area-conservative downscaling to 4km, adjacent 0.25 deg
LUH2 cells can carry different cumulative harvest amounts, which shows up as
patch boundaries in this panel that align with the 0.25 deg grid (verified
by overlay), unlike GPP/NPP which are smooth at 4km. So some of this panel's
apparent spatial detail reflects the coarser harvest forcing, not genuinely
resolved 4km heterogeneity.

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
number of layers. The 0-100 cm panel uses TOTSOMC_1m as-is (the model's own
0-1 m integral). The full-profile panel uses TOTSOMC as-is (the model's own
full-column integral, over all 15 levdcmp layers -- this run's DZSOI puts
the bottom of layer 15 at ~42.1 m, the nominal depth of ELM's 15-layer soil
column, though most SOM is concentrated far above that).

Usage
-----
    python plot_gpp_npp_soilc_maps.py
"""

import os
import sys

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.io import find_h0_files
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

# Same brown-teal, white-dropped BrBG scheme + fixed 0-20 kgC/m^2 scale used
# in wildfires/ELM_results4CCSImidmeet/plot_SOC.R, so the SoilC panels here
# read consistently with that project's SOC_comparison.png.
BRBG_NO_WHITE = LinearSegmentedColormap.from_list(
    "BrBG_no_white",
    [c for i, c in enumerate(plt.get_cmap("BrBG")(np.linspace(0, 1, 9))) if i != 4],
    N=256,
)
SOC_VMIN, SOC_VMAX = 0, 20

# 0.25 deg / ~0.0417 deg native spacing =~ 6 grid cells
BIOMASS_SMOOTH_SIGMA_CELLS = 1.5


# ── Helpers ──────────────────────────────────────────────────────────────

def load_yearly_vars(files: list[str], varnames: list[str]) -> xr.Dataset:
    """Open each year's h0 file, keep only *varnames* (+ time), and concat
    along time. Deliberately avoids xr.open_mfdataset: the project's conda
    env (make_surfdata_pf) has no dask, and the selected variables are small
    enough (a handful of MB per file) to just load and concat directly."""
    per_var = {v: [] for v in varnames}
    for f in files:
        with xr.open_dataset(f, decode_times=True) as ds:
            for v in varnames:
                per_var[v].append(ds[v].load())
    return xr.Dataset({v: xr.concat(das, dim="time") for v, das in per_var.items()})


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


def annual_mean_pool_map(ds: xr.Dataset, var: str) -> xr.DataArray:
    """Pool/state variable, monthly records -> per-calendar-year mean, dims
    (year, lat, lon). Plain time-mean (no day-weighting -- not a flux)."""
    da = shift_time_back_one_month(ds)[var]
    true_years = np.array([t.year for t in da["time"].values])
    yearly = []
    for yr in np.unique(true_years):
        yr_mean = da.isel(time=np.where(true_years == yr)[0]).mean(dim="time", skipna=True)
        yearly.append(yr_mean.assign_coords(year=int(yr)))
    return xr.concat(yearly, dim="year")


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50) -> BoundaryNorm:
    """Equal-population (quantile) color bins -- see
    plot_biomass_soc_comparison.py's copy of this function for the full
    rationale (concentrates color steps where the data actually is, without
    n_levels so small that a real gentle gradient collapses into one flat,
    hard-edged bin)."""
    finite = data[np.isfinite(data)]
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    return BoundaryNorm(edges, ncolors=256)


def smooth_for_display(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian-smooth a lat/lon map for display only, NaN-aware.

    TOTVEGC_ABG carries visible patch boundaries that align with the 0.25 deg
    LUH2 wood-harvest grid (adjacent coarse cells can have different
    cumulative harvest history -- see module docstring). This softens those
    sharp edges into gradual transitions for this one figure; it does not
    touch the underlying data used anywhere else (ELM_biomass_soc_for_
    comparison.nc, the *_2023 SoilC panels, etc).

    Uses normalized convolution (smooth the data with NaNs set to 0, smooth
    a 0/1 valid-data mask the same way, divide) so land/ocean edges don't
    bleed NaN into valid cells or get pulled toward zero.
    """
    valid = np.isfinite(arr)
    filled = np.where(valid, arr, 0.0)
    weight = valid.astype(float)

    smoothed_vals = gaussian_filter(filled, sigma=sigma)
    smoothed_weight = gaussian_filter(weight, sigma=sigma)

    with np.errstate(invalid="ignore", divide="ignore"):
        out = smoothed_vals / smoothed_weight
    out[smoothed_weight < 0.5] = np.nan  # don't extrapolate far past the coast
    return out


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
    ds_flux = load_yearly_vars(files, ["GPP", "NPP", "TOTVEGC_ABG"])
    lat = ds_flux["lat"].values
    lon = ds_flux["lon"].values

    gpp_yearly = annual_total_flux_map(ds_flux, "GPP")
    npp_yearly = annual_total_flux_map(ds_flux, "NPP")
    print(f"  GPP yearly totals cover years: {gpp_yearly['year'].values.tolist()}")

    gpp_10yr = gpp_yearly.mean(dim="year", skipna=True).values
    npp_10yr = npp_yearly.mean(dim="year", skipna=True).values

    # ---- Biomass: same 2014-2023 years as GPP/NPP ------------------------
    biomass_yearly = annual_mean_pool_map(ds_flux, "TOTVEGC_ABG")  # gC/m^2
    biomass_10yr_kgC = biomass_yearly.mean(dim="year", skipna=True).values / 1000.0
    # display-only smoothing to soften the 0.25 deg LUH2 harvest-grid patch
    # boundaries (see module docstring / smooth_for_display docstring)
    biomass_10yr_kgC_smoothed = smooth_for_display(biomass_10yr_kgC, BIOMASS_SMOOTH_SIGMA_CELLS)
    biomass_norm = quantile_boundary_norm(biomass_10yr_kgC_smoothed, n_levels=50)
    # unsmoothed version too, for a like-for-like series with the 1850/2000
    # panels (which have no smoothing applied) showing the block pattern
    # actually building up over the run
    biomass_raw_norm = quantile_boundary_norm(biomass_10yr_kgC, n_levels=50)

    # ---- Soil C: end-of-run (Dec 2023) snapshot ---------------------------
    last_file = files[-1]  # 2023-02-01 file: records true Jan-Dec 2023 after shift
    ds_soil = xr.open_dataset(last_file, decode_times=True)
    ds_soil_shifted = shift_time_back_one_month(ds_soil)
    true_months = [t.month for t in ds_soil_shifted["time"].values]
    dec_idx = true_months.index(12)
    dec2023 = ds_soil_shifted.isel(time=dec_idx)

    totsomc_full_gC = dec2023["TOTSOMC"].values           # gC/m^2, model's own full-profile integral
    soilc_full_kgC = totsomc_full_gC / 1000.0

    totsomc_1m_gC = dec2023["TOTSOMC_1m"].values           # gC/m^2, model's own 0-100cm integral
    soilc_1m_kgC = totsomc_1m_gC / 1000.0

    first_file = find_h0_files(RUN_DIR, year_min=1850, year_max=1850)[0]
    ds_static = xr.open_dataset(first_file, decode_times=True)
    dzsoi = ds_static["DZSOI"]                             # (levgrnd, lat, lon), m
    soilc_030_gC = soilc_0_30cm(dec2023, dzsoi)
    soilc_030_kgC = soilc_030_gC / 1000.0

    # ---- Biomass, 1850: run's first year, before decades of harvest could
    # accumulate into the 0.25 deg LUH2 block pattern (see module docstring)
    biomass_1850_yearly = annual_mean_pool_map(ds_static, "TOTVEGC_ABG")  # gC/m^2, dims (year=1, lat, lon)
    biomass_1850_kgC = biomass_1850_yearly.isel(year=0).values / 1000.0
    biomass_1850_norm = quantile_boundary_norm(biomass_1850_kgC, n_levels=50)
    ds_static.close()

    # ---- Biomass, 2000: 150 years in -- harvest has had time to accumulate
    year2000_file = find_h0_files(RUN_DIR, year_min=2000, year_max=2000)[0]
    ds_2000 = xr.open_dataset(year2000_file, decode_times=True)
    biomass_2000_yearly = annual_mean_pool_map(ds_2000, "TOTVEGC_ABG")  # gC/m^2
    biomass_2000_kgC = biomass_2000_yearly.isel(year=0).values / 1000.0
    biomass_2000_norm = quantile_boundary_norm(biomass_2000_kgC, n_levels=50)
    ds_2000.close()

    # mask non-land with landmask from the soil dataset
    landmask = ds_soil["landmask"].values if "landmask" in ds_soil else None
    if landmask is not None:
        land_nan = np.where(landmask == 1, 1.0, np.nan)
        soilc_full_kgC = soilc_full_kgC * land_nan
        soilc_1m_kgC = soilc_1m_kgC * land_nan
        soilc_030_kgC = soilc_030_kgC * land_nan
    ds_soil.close()

    # ---- Report + plot ------------------------------------------------
    panels = [
        {
            "data": gpp_10yr, "var": "GPP", "label": "GPP",
            "title": f"GPP — {YEAR_MIN}-{YEAR_MAX} mean annual total",
            "units": "gC/m^2/year", "cmap": "YlGn",
            "fname": f"GPP_{YEAR_MIN}-{YEAR_MAX}mean",
        },
        {
            "data": npp_10yr, "var": "NPP", "label": "NPP",
            "title": f"NPP — {YEAR_MIN}-{YEAR_MAX} mean annual total",
            "units": "gC/m^2/year", "cmap": "YlGn",
            "fname": f"NPP_{YEAR_MIN}-{YEAR_MAX}mean",
        },
        {
            "data": biomass_10yr_kgC_smoothed, "var": "Biomass", "label": "Aboveground biomass (TOTVEGC_ABG)",
            "title": f"Aboveground biomass — {YEAR_MIN}-{YEAR_MAX} mean",
            "units": "kgC/m^2", "cmap": "viridis", "norm": biomass_norm,
            "fname": f"Biomass_{YEAR_MIN}-{YEAR_MAX}mean",
        },
        {
            "data": biomass_1850_kgC, "var": "Biomass_1850", "label": "Aboveground biomass (TOTVEGC_ABG)",
            "title": "Aboveground biomass — 1850",
            "units": "kgC/m^2", "cmap": "viridis", "norm": biomass_1850_norm,
            "fname": "Biomass_1850",
        },
        {
            "data": biomass_10yr_kgC, "var": "Biomass_2014-2023_raw", "label": "Aboveground biomass (TOTVEGC_ABG)",
            "title": f"Aboveground biomass — {YEAR_MIN}-{YEAR_MAX} mean (unsmoothed)",
            "units": "kgC/m^2", "cmap": "viridis", "norm": biomass_raw_norm,
            "fname": f"Biomass_{YEAR_MIN}-{YEAR_MAX}mean_raw",
        },
        {
            "data": biomass_2000_kgC, "var": "Biomass_2000", "label": "Aboveground biomass (TOTVEGC_ABG)",
            "title": "Aboveground biomass — 2000",
            "units": "kgC/m^2", "cmap": "viridis", "norm": biomass_2000_norm,
            "fname": "Biomass_2000",
        },
        {
            "data": soilc_030_kgC, "var": "SoilC_0-30cm", "label": "Soil organic C (0-30 cm)",
            "title": "Soil organic C, 0-30 cm — end of run (Dec 2023)",
            "units": "kgC/m^2", "cmap": BRBG_NO_WHITE, "vmin": SOC_VMIN, "vmax": SOC_VMAX,
            "fname": "SoilC_0-30cm_2023",
        },
        {
            "data": soilc_1m_kgC, "var": "SoilC_0-100cm", "label": "Soil organic C (0-100 cm)",
            "title": "Soil organic C, 0-100 cm — end of run (Dec 2023)",
            "units": "kgC/m^2", "cmap": BRBG_NO_WHITE, "vmin": SOC_VMIN, "vmax": SOC_VMAX,
            "fname": "SoilC_0-100cm_2023",
        },
        {
            "data": soilc_full_kgC, "var": "SoilC_fullprofile", "label": "Soil organic C (full profile)",
            "title": "Soil organic C, full profile — end of run (Dec 2023)",
            "units": "kgC/m^2", "cmap": BRBG_NO_WHITE, "vmin": SOC_VMIN, "vmax": SOC_VMAX,
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
            vmin=p.get("vmin"),
            vmax=p.get("vmax"),
            norm=p.get("norm"),
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
