"""
Re-plot the harvfix GPP/NPP/SoilC showcase maps with US state boundaries.

The Pathfinder conda env used for the Slurm job (make_surfdata_pf) has no
cartopy, so plot_gpp_npp_soilc_maps.py fell back to plain matplotlib axes
(no coastlines/state borders). This script re-reads the GeoTIFFs that job
already produced (and that were rsync'd back to this Mac) and re-saves the
PNGs using elmtools.plot.plot_2d_map's cartopy path, which this Mac's local
venv supports.

Run **locally** (not via ssh/Slurm) with the local venv that has cartopy:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python replot_with_states_local.py
"""

import os
import sys

import numpy as np
import rioxarray as rxr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from elmtools.plot import plot_2d_map

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

# Same brown-teal, white-dropped BrBG scheme + fixed 0-20 kgC/m^2 scale used
# in wildfires/ELM_results4CCSImidmeet/plot_SOC.R and
# plot_biomass_soc_comparison.py's SOC_comparison_harvfix.png, so the SoilC
# panels here read consistently with that figure.
BRBG_NO_WHITE = LinearSegmentedColormap.from_list(
    "BrBG_no_white",
    [c for i, c in enumerate(plt.get_cmap("BrBG")(np.linspace(0, 1, 9))) if i != 4],
    N=256,
)
SOC_VMIN, SOC_VMAX = 0, 20


def quantile_boundary_norm(data: np.ndarray, n_levels: int = 50) -> BoundaryNorm:
    """Equal-population (quantile) color bins -- see
    plot_biomass_soc_comparison.py / plot_gpp_npp_soilc_maps.py for the
    rationale."""
    finite = data[np.isfinite(data)]
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    return BoundaryNorm(edges, ncolors=256)


PANELS = [
    {"fname": "GPP_2014-2023mean", "label": "GPP", "units": "gC/m^2/year", "cmap": "YlGn",
     "title": "GPP — 2014-2023 mean annual total"},
    {"fname": "NPP_2014-2023mean", "label": "NPP", "units": "gC/m^2/year", "cmap": "YlGn",
     "title": "NPP — 2014-2023 mean annual total"},
    {"fname": "Biomass_2014-2023mean", "label": "Aboveground biomass (TOTVEGC_ABG)", "units": "kgC/m^2",
     "cmap": "viridis", "quantile_norm": True,
     "title": "Aboveground biomass — 2014-2023 mean"},
    {"fname": "Biomass_1850", "label": "Aboveground biomass (TOTVEGC_ABG)", "units": "kgC/m^2",
     "cmap": "viridis", "quantile_norm": True,
     "title": "Aboveground biomass — 1850"},
    {"fname": "SoilC_0-30cm_2023", "label": "Soil organic C (0-30 cm)", "units": "kgC/m^2",
     "cmap": BRBG_NO_WHITE, "vmin": SOC_VMIN, "vmax": SOC_VMAX,
     "title": "Soil organic C, 0-30 cm — end of run (Dec 2023)"},
    {"fname": "SoilC_0-100cm_2023", "label": "Soil organic C (0-100 cm)", "units": "kgC/m^2",
     "cmap": BRBG_NO_WHITE, "vmin": SOC_VMIN, "vmax": SOC_VMAX,
     "title": "Soil organic C, 0-100 cm — end of run (Dec 2023)"},
    {"fname": "SoilC_fullprofile_2023", "label": "Soil organic C (full profile)", "units": "kgC/m^2",
     "cmap": BRBG_NO_WHITE, "vmin": SOC_VMIN, "vmax": SOC_VMAX,
     "title": "Soil organic C, full profile — end of run (Dec 2023)"},
]


def main():
    for p in PANELS:
        tif_path = os.path.join(OUT_DIR, f"{p['fname']}.tif")
        da = rxr.open_rasterio(tif_path).squeeze("band", drop=True)
        lat = da["y"].values
        lon = da["x"].values
        arr = da.values.astype(float)
        nodata = da.rio.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)

        norm = quantile_boundary_norm(arr) if p.get("quantile_norm") else None

        png_path = os.path.join(OUT_DIR, f"{p['fname']}.png")
        plot_2d_map(
            arr, lat, lon,
            var_name=p["label"],
            title=p["title"],
            outfile=png_path,
            cmap=p["cmap"],
            vmin=p.get("vmin"),
            vmax=p.get("vmax"),
            norm=norm,
            figsize=(10, 6),
            units=p["units"],
            add_coastlines=True,
            add_states=True,
            add_borders=True,
            add_gridlines=True,
            set_extent=True,
        )


if __name__ == "__main__":
    main()
