"""
Rebuild wildfires/ELM_results4CCSImidmeet's Biomass_comparison.png and
SOC_comparison.png with the "ELM" panel replaced by the harvfix run
(20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC), instead
of the older Southeast-hires run the originals used (see plot_Biomass.R /
plot_SOC.R in that project for the original recipe).

Reuses the observational products already prepared there, unchanged:
  - Biomass: otherdata00/biomass/ESACCI/biomass_masked_kgm2.nc
             (8 bands = years [2010, 2014..2020]; mean of 2014-2020 used)
  - SOC:     otherdata00/soc/soilgrids/OCD_total_0_100cm_kg_m2.tif  (0-100cm)
             otherdata00/soc/HWSD_1247/soc_1m_kg_m2.nc              (0-100cm)

Run **locally** (not via ssh/Slurm) with the local venv that has
cartopy/rioxarray, after pulling extract_biomass_soc.py's output back:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_biomass_soc_comparison.py
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
CASE = "20260723_Southeast_hires_s7P_s8hdmfix_harvfix_ICB20TRCNPRDCTCBC"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "outputs")
ELM_NC = os.path.join(OUT_DIR, "ELM_biomass_soc_for_comparison.nc")

WILDFIRES_DIR = "/Users/zw5/ORNL_workplace/wildfires/ELM_results4CCSImidmeet"
ESACCI_NC = os.path.join(WILDFIRES_DIR, "otherdata00/biomass/ESACCI/biomass_masked_kgm2.nc")
SOILGRIDS_TIF = os.path.join(WILDFIRES_DIR, "otherdata00/soc/soilgrids/OCD_total_0_100cm_kg_m2.tif")
HWSD_NC = os.path.join(WILDFIRES_DIR, "otherdata00/soc/HWSD_1247/soc_1m_kg_m2.nc")

ESACCI_YEARS = [2010, 2014, 2015, 2016, 2017, 2018, 2019, 2020]  # Band1..Band8, per plot_Biomass.R
ESACCI_COMBINE_YEARS = [2014, 2015, 2016, 2017, 2018, 2019, 2020]

LON_MIN, LON_MAX = -95.5, -73.5
LAT_MIN, LAT_MAX = 24.5, 38.0

BRBG_NO_WHITE = LinearSegmentedColormap.from_list(
    "BrBG_no_white",
    [c for i, c in enumerate(plt.get_cmap("BrBG")(np.linspace(0, 1, 9))) if i != 4],
    N=256,
)


# ── Helpers ─────────────────────────────────────────────────────────────

def crop(da: xr.DataArray, lat_name="lat", lon_name="lon") -> xr.DataArray:
    return da.sel(
        {lat_name: slice(LAT_MIN, LAT_MAX), lon_name: slice(LON_MIN, LON_MAX)}
    )


def load_elm():
    ds = xr.open_dataset(ELM_NC)
    return crop(ds["TOTVEGC_ABG_mean"]), crop(ds["TOTSOMC_1m_mean"])


def load_esacci_biomass():
    ds = xr.open_dataset(ESACCI_NC)
    bands = [f"Band{ESACCI_YEARS.index(y) + 1}" for y in ESACCI_COMBINE_YEARS]
    stacked = xr.concat([ds[b] for b in bands], dim="year")
    mean = stacked.mean(dim="year", skipna=True)
    return crop(mean)


def load_soilgrids_soc():
    da = rxr.open_rasterio(SOILGRIDS_TIF).squeeze("band", drop=True)
    da = da.rename({"x": "lon", "y": "lat"})
    da = da.where(da >= 0)  # matches plot_SOC.R: soilgrids_cropped[soilgrids_cropped < 0] <- NA
    # rioxarray's y (lat) is north->south descending; make ascending like the others
    da = da.sortby("lat")
    return crop(da)


def load_hwsd_soc():
    ds = xr.open_dataset(HWSD_NC)
    var = list(ds.data_vars)[0]
    return crop(ds[var])


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 12) -> BoundaryNorm:
    """Bin edges at equal *population* (quantile) steps rather than equal
    value steps. Most biomass pixels sit in a narrow low-to-mid range with a
    long high tail, so an equal-value scale spends most of its color range
    on the rare high pixels and leaves the bulk of the map looking like one
    shade. Equal-population bins instead give the densely-populated range
    its fair share of distinct colors, so the pixel-to-pixel texture (the
    thing high-res actually buys you) becomes visible instead of washed
    out."""
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
    ax.set_title(title)
    return mesh


def make_comparison_figure(panels, cbar_label, out_path, figsize, extend="both"):
    fig, axes = plt.subplots(
        1, len(panels), figsize=figsize,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    if len(panels) == 1:
        axes = [axes]
    mesh = None
    for ax, p in zip(axes, panels):
        mesh = panel(ax, p["data"], p["title"], p["cmap"],
                     vmin=p.get("vmin"), vmax=p.get("vmax"), norm=p.get("norm"))
    fig.colorbar(mesh, ax=axes, label=cbar_label, pad=0.02, shrink=0.85, extend=extend)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    elm_biomass, elm_soc = load_elm()
    esacci = load_esacci_biomass()
    soilgrids = load_soilgrids_soc()
    hwsd = load_hwsd_soc()

    # ---- Biomass comparison: shared quantile (equal-population) color scale ----
    # Equal-value scales (e.g. a plain 1st-99th pct linear stretch) bury the
    # fine spatial texture high-res is supposed to show, because most pixels
    # land in a narrow band and get nearly the same color. Quantile bins
    # fix that -- see quantile_boundary_norm().
    combined = np.concatenate([elm_biomass.values.ravel(), esacci.values.ravel()])
    biomass_norm = quantile_boundary_norm(combined, n_levels=12)

    make_comparison_figure(
        panels=[
            {"data": elm_biomass, "title": "ELM Mean (2014-2020)", "cmap": "viridis", "norm": biomass_norm},
            {"data": esacci, "title": "ESACCI Mean (2014-2020)", "cmap": "viridis", "norm": biomass_norm},
        ],
        cbar_label="Biomass (kg C m$^{-2}$)",
        out_path=os.path.join(OUT_DIR, "Biomass_comparison_harvfix.png"),
        figsize=(12, 6),
        extend="neither",
    )

    # ---- SOC comparison: fixed 0-20 scale, BrBG-no-white, like plot_SOC.R ----
    make_comparison_figure(
        panels=[
            {"data": elm_soc, "title": "ELM Mean SOC (2000-2020) (0-100cm)", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": 20},
            {"data": soilgrids, "title": "SoilGrids SOC (0-100cm)", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": 20},
            {"data": hwsd, "title": "HWSD SOC (0-100cm)", "cmap": BRBG_NO_WHITE, "vmin": 0, "vmax": 20},
        ],
        cbar_label="SOC (kg C m$^{-2}$)",
        out_path=os.path.join(OUT_DIR, "SOC_comparison_harvfix.png"),
        figsize=(17, 6),
    )


if __name__ == "__main__":
    main()
