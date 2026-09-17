"""
Poster Panel 2: biomass and soil organic carbon (0-30 cm), colorbar along
the bottom. Produces two variants of each:
  - three columns (0.5 deg ELM | 4 km ELM | observations)
  - two columns (4 km ELM | observations only, 2026-09-17 addition), for a
    poster slot that wants just the high-res-vs-obs comparison without the
    0.5deg column.

Runs **locally** (not via ssh/Slurm) with the venv that has cartopy/rioxarray
-- same one used by
../../20260723_..._harvfix/plot_biomass_soc_comparison.py:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_biomass_soc_panel.py

Prerequisites (pulled back from Pathfinder first):
    _cache/ELM_biomass_soc_0_30cm_4km.nc
    _cache/ELM_biomass_soc_0_30cm_0.5deg.nc
(produced by extract_biomass_soc.py via submit_py.sbatch)

Observations, reused unchanged from
../../20260723_..._harvfix/plot_biomass_soc_comparison.py's own loaders/
conventions (same crop box, same masking):
  - Biomass: ESA-CCI biomass_masked_kgm2.nc, mean of 2014-2020 bands.
  - SOC 0-30 cm: SoilGrids' own native 0-5/5-15/15-30 cm depth layers
    (ocd_*.tif), summed with the same hg/m^3 -> kg/m^3 conversion factor
    (10) and layer-thickness weights used by
    wildfires/ELM_results4CCSImidmeet/process_soilgrids.py's 0-100cm
    product -- there is no precomputed 0-30cm SoilGrids product on disk,
    so this reproduces just the first three of that script's five terms.
    HWSD's AWT_S_SOC.nc4 ("topsoil", SUM_s_c_1) is *also* a 0-30cm figure
    per HWSD's own S/T topsoil/subsoil split (see
    wildfires/ELM_results4CCSImidmeet/process_HWSD_1247.py) but is not
    used here since the panel layout only has one "observations" column;
    SoilGrids is used as the primary because it matches the exact 0-30cm
    depth breaks natively (250m native res) with no S/T assumption.

Caveat (RESULTS_SUMMARY.md, external review, 2026-09-15): the project has
not yet done a full, depth/mask/unit-reconciled observational benchmark.
This panel is illustrative, not a formal validation -- caption it that way.
"""
import os

import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSTER_DIR = os.path.dirname(SCRIPT_DIR)
CACHE_DIR = os.path.join(POSTER_DIR, "_cache")
OUT_DIR = os.path.join(POSTER_DIR, "outputs")

ELM_4KM_NC = os.path.join(CACHE_DIR, "ELM_biomass_soc_0_30cm_4km.nc")
ELM_HALFDEG_NC = os.path.join(CACHE_DIR, "ELM_biomass_soc_0_30cm_0.5deg.nc")

WILDFIRES_DIR = "/Users/zw5/ORNL_workplace/wildfires/ELM_results4CCSImidmeet"
ESACCI_NC = os.path.join(WILDFIRES_DIR, "otherdata00/biomass/ESACCI/biomass_masked_kgm2.nc")
SOILGRIDS_DIR = os.path.join(WILDFIRES_DIR, "otherdata00/soc/soilgrids")

ESACCI_YEARS = [2010, 2014, 2015, 2016, 2017, 2018, 2019, 2020]  # Band1..Band8
ESACCI_COMBINE_YEARS = [2014, 2015, 2016, 2017, 2018, 2019, 2020]

# SoilGrids 0-30cm = sum of the first three depth layers, same conversion
# factor and thickness convention as process_soilgrids.py's 0-100cm product.
SOILGRIDS_LAYERS_0_30CM = {
    "ocd_0-5cm_mean.tif": 0.05,
    "ocd_5-15cm_mean.tif": 0.10,
    "ocd_15-30cm_mean.tif": 0.15,
}
SOILGRIDS_CONVERSION_FACTOR = 10  # hg/m^3 -> kg/m^3, per process_soilgrids.py

LON_MIN, LON_MAX = -95.5, -73.5
LAT_MIN, LAT_MAX = 24.5, 38.0

BRBG_NO_WHITE = LinearSegmentedColormap.from_list(
    "BrBG_no_white",
    [c for i, c in enumerate(plt.get_cmap("BrBG")(np.linspace(0, 1, 9))) if i != 4],
    N=256,
)


# ── Helpers ─────────────────────────────────────────────────────────────

def crop(da: xr.DataArray, lat_name="lat", lon_name="lon") -> xr.DataArray:
    return da.sel({lat_name: slice(LAT_MIN, LAT_MAX), lon_name: slice(LON_MIN, LON_MAX)})


def load_elm(nc_path: str):
    """TOTVEGC_ABG carries NaN over ocean/inactive gridcells, but the raw
    SOIL1-4C_vr pools summed into SOC_0_30cm_mean are hard 0.0 there
    (confirmed: every NaN-biomass cell has SOC exactly 0.0) -- without
    masking, ocean renders as solid vmin-color instead of blank. Reuse the
    biomass NaN pattern as the land mask for SOC."""
    ds = xr.open_dataset(nc_path)
    biomass = crop(ds["TOTVEGC_ABG_mean"])
    soc = crop(ds["SOC_0_30cm_mean"]).where(~np.isnan(biomass))
    return biomass, soc


def load_esacci_biomass() -> xr.DataArray:
    ds = xr.open_dataset(ESACCI_NC)
    bands = [f"Band{ESACCI_YEARS.index(y) + 1}" for y in ESACCI_COMBINE_YEARS]
    stacked = xr.concat([ds[b] for b in bands], dim="year")
    mean = stacked.mean(dim="year", skipna=True)
    return crop(mean)


def load_soilgrids_soc_0_30cm() -> xr.DataArray:
    total = None
    for fname, thickness_m in SOILGRIDS_LAYERS_0_30CM.items():
        da = rxr.open_rasterio(os.path.join(SOILGRIDS_DIR, fname)).squeeze("band", drop=True)
        da = da.rename({"x": "lon", "y": "lat"})
        stock = (da / SOILGRIDS_CONVERSION_FACTOR) * thickness_m  # kg/m^2 for this layer
        total = stock if total is None else total + stock
    total = total.where(total >= 0)  # drop the -32768 nodata sentinel, same convention as the 1m product
    total = total.sortby("lat")      # rioxarray's y is north->south descending
    return crop(total)


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50) -> BoundaryNorm:
    """Equal-population (quantile) bin edges -- see the sibling harvfix
    plot_biomass_soc_comparison.py for the full rationale: an equal-value
    scale buries the pixel-to-pixel texture that high resolution is
    supposed to show."""
    finite = data[np.isfinite(data)]
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    return BoundaryNorm(edges, ncolors=256)


def panel(ax, da, title, cmap, vmin=None, vmax=None, norm=None):
    lon = da["lon"].values
    lat = da["lat"].values
    mesh = ax.pcolormesh(
        lon, lat, da.values, vmin=vmin, vmax=vmax, norm=norm, cmap=cmap,
        shading="auto", transform=ccrs.PlateCarree(),
    )
    ax.coastlines(resolution="10m", linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
    ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.5, linestyle="--")
    ax.set_title(title, fontsize=11)
    return mesh


def make_panel_figure(panels, cbar_label, out_path, figsize, extend="both"):
    """1 row x N columns (N = len(panels)), shared horizontal colorbar along the bottom.
    Let matplotlib place the colorbar relative to the actual (aspect-
    locked) geoaxes rather than a hardcoded figure-fraction box -- a fixed
    box leaves a large blank gap because cartopy shrinks each PlateCarree
    axes to match the domain's true lon/lat aspect ratio."""
    fig, axes = plt.subplots(
        1, len(panels), figsize=figsize,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    mesh = None
    for ax, p in zip(axes, panels):
        mesh = panel(ax, p["data"], p["title"], p["cmap"],
                     vmin=p.get("vmin"), vmax=p.get("vmax"), norm=p.get("norm"))
    fig.colorbar(mesh, ax=axes, orientation="horizontal", label=cbar_label,
                 pad=0.06, shrink=0.6, aspect=35, extend=extend)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    elm_4km_biomass, elm_4km_soc = load_elm(ELM_4KM_NC)
    elm_halfdeg_biomass, elm_halfdeg_soc = load_elm(ELM_HALFDEG_NC)
    esacci = load_esacci_biomass()
    soilgrids = load_soilgrids_soc_0_30cm()

    # ---- Biomass: shared quantile color scale across all 3 panels ----
    combined = np.concatenate([
        elm_halfdeg_biomass.values.ravel(),
        elm_4km_biomass.values.ravel(),
        esacci.values.ravel(),
    ])
    biomass_norm = quantile_boundary_norm(combined, n_levels=50)

    make_panel_figure(
        panels=[
            {"data": elm_halfdeg_biomass, "title": "0.5° ELM (2014-2020 mean)", "cmap": "viridis", "norm": biomass_norm},
            {"data": elm_4km_biomass, "title": "4 km ELM (2014-2020 mean)", "cmap": "viridis", "norm": biomass_norm},
            {"data": esacci, "title": "ESA-CCI obs (2014-2020 mean)", "cmap": "viridis", "norm": biomass_norm},
        ],
        cbar_label="Aboveground biomass (kg C m$^{-2}$)",
        out_path=os.path.join(OUT_DIR, "panel2_biomass_0.5deg_4km_obs.png"),
        figsize=(15, 6),
        extend="neither",
    )

    # ---- Biomass, 4km-only variant (2026-09-17): drop 0.5deg, keep just
    # 4km ELM vs obs. Recomputes its own quantile norm from only the two
    # fields actually plotted, rather than reusing biomass_norm above
    # (which was fit including 0.5deg's more compressed value range) --
    # the color scale should reflect what's on the page, not a dropped
    # panel's influence on it.
    combined_4km = np.concatenate([elm_4km_biomass.values.ravel(), esacci.values.ravel()])
    biomass_norm_4km = quantile_boundary_norm(combined_4km, n_levels=50)
    make_panel_figure(
        panels=[
            {"data": elm_4km_biomass, "title": "4 km ELM (2014-2020 mean)", "cmap": "viridis", "norm": biomass_norm_4km},
            {"data": esacci, "title": "ESA-CCI obs (2014-2020 mean)", "cmap": "viridis", "norm": biomass_norm_4km},
        ],
        cbar_label="Aboveground biomass (kg C m$^{-2}$)",
        out_path=os.path.join(OUT_DIR, "panel2_biomass_4km_obs.png"),
        figsize=(10, 6),
        extend="neither",
    )

    # ---- SOC 0-30cm: shared fixed scale (robust 98th pct across all 3) ----
    combined_soc = np.concatenate([
        elm_halfdeg_soc.values.ravel(),
        elm_4km_soc.values.ravel(),
        soilgrids.values.ravel(),
    ])
    soc_vmax = float(np.nanpercentile(combined_soc, 98))
    print(f"SOC 0-30cm shared color scale: 0 to {soc_vmax:.2f} kgC/m^2 (98th pct of all 3 panels)")

    make_panel_figure(
        panels=[
            {"data": elm_halfdeg_soc, "title": "0.5° ELM (2014-2020 mean)", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": soc_vmax},
            {"data": elm_4km_soc, "title": "4 km ELM (2014-2020 mean)", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": soc_vmax},
            {"data": soilgrids, "title": "SoilGrids obs", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": soc_vmax},
        ],
        cbar_label="SOC 0-30cm (kg C m$^{-2}$)",
        out_path=os.path.join(OUT_DIR, "panel2_soc_0_30cm_0.5deg_4km_obs.png"),
        figsize=(15, 6),
    )

    # ---- SOC, 4km-only variant (2026-09-17): drop 0.5deg, keep just 4km
    # ELM vs SoilGrids. Own vmax from just these two fields, same reasoning
    # as the biomass 4km-only variant above.
    combined_soc_4km = np.concatenate([elm_4km_soc.values.ravel(), soilgrids.values.ravel()])
    soc_vmax_4km = float(np.nanpercentile(combined_soc_4km, 98))
    print(f"SOC 0-30cm (4km-only) color scale: 0 to {soc_vmax_4km:.2f} kgC/m^2 (98th pct of 2 panels)")
    make_panel_figure(
        panels=[
            {"data": elm_4km_soc, "title": "4 km ELM (2014-2020 mean)", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": soc_vmax_4km},
            {"data": soilgrids, "title": "SoilGrids obs", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": soc_vmax_4km},
        ],
        cbar_label="SOC 0-30cm (kg C m$^{-2}$)",
        out_path=os.path.join(OUT_DIR, "panel2_soc_0_30cm_4km_obs.png"),
        figsize=(10, 6),
    )


if __name__ == "__main__":
    main()
