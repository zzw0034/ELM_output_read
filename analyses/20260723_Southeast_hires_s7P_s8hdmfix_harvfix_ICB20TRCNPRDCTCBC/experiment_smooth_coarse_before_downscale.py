"""
Experiment: what would "smooth the 0.25 deg coarse field before downscaling"
(Option 1 from the harvest-forcing discussion) actually look like, for 2010?

Method (a shortcut that avoids re-deriving the PFT-based forest weights from
scratch, using only files we already have locally):

  1. Take the real LUH2 0.25 deg source field F_coarse (already extracted:
     LUH2source_AnnualHarvest_2010.tif) and the real downscaled 4km field
     D (already extracted: AnnualHarvest_2010.tif).
  2. Back out the LOCAL REDISTRIBUTION SHAPE that the real downscaling
     applied within each 0.25 deg cell: S = D / F_coarse_at_fine_cell.
     (This *is* the local forest-weight pattern the real pipeline used,
     just recovered empirically instead of re-reading the PFT file.)
  3. Gaussian-smooth F_coarse on the COARSE grid (removes the sharp
     between-cell jump), then continuously (bilinear) upsample it onto the
     fine grid -- this is the "smoothed F_coarse, still downscaled with the
     same shape" amplitude field.
  4. Where a fine cell's home coarse cell had F_coarse=0 (S undefined,
     since D is also 0 there), fill S from nearby cells via the same
     NaN-aware normalized-convolution trick used for the earlier display
     smoothing -- so cells that gain harvest from the coarse smoothing
     still get a plausible local texture instead of being flat.
  5. New field = smoothed-and-upsampled F_coarse * filled S.

Reads the GeoTIFFs already local; run **locally**:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python experiment_smooth_coarse_before_downscale.py
"""

import os

import numpy as np
import rioxarray as rxr
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
YEAR = 2010
COARSE_SMOOTH_SIGMA_CELLS = 1.0   # in 0.25 deg coarse-grid cells
TEXTURE_FILL_SIGMA_FINE_CELLS = 6.0  # ~1 coarse cell, in 4km fine-grid cells

LON_MIN, LON_MAX = -95.5, -73.5
LAT_MIN, LAT_MAX = 24.5, 38.0


def load_tif(fname):
    """Load a GeoTIFF and return (data, lat, lon) with lat strictly
    ASCENDING (GeoTIFFs are north-up, i.e. descending lat, which breaks
    RegularGridInterpolator -- must sort+flip here)."""
    da = rxr.open_rasterio(os.path.join(OUT_DIR, fname)).squeeze("band", drop=True)
    lat = da["y"].values
    lon = da["x"].values
    arr = da.values.astype(float)
    nodata = da.rio.nodata
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    if lat[0] > lat[-1]:
        lat = lat[::-1]
        arr = arr[::-1, :]
    return arr, lat, lon


def normalized_conv_fill(arr, sigma):
    valid = np.isfinite(arr)
    filled = np.where(valid, arr, 0.0)
    weight = valid.astype(float)
    sv = gaussian_filter(filled, sigma=sigma)
    sw = gaussian_filter(weight, sigma=sigma)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = sv / sw
    out[sw < 1e-6] = np.nan
    return out


def quantile_boundary_norm(data, n_levels=50):
    finite = data[np.isfinite(data)]
    edges = np.unique(np.quantile(finite, np.linspace(0, 1, n_levels + 1)))
    return BoundaryNorm(edges, ncolors=256)


def main():
    coarse, clat, clon = load_tif(f"LUH2source_AnnualHarvest_{YEAR}.tif")
    fine, flat, flon = load_tif(f"AnnualHarvest_{YEAR}.tif")
    coarse = np.nan_to_num(coarse, nan=0.0)

    # ---- step 2: recover local shape S = D / F_coarse_at_fine_cell --------
    coarse_at_fine_interp = RegularGridInterpolator(
        (clat, clon), coarse, method="nearest", bounds_error=False, fill_value=0.0
    )
    flon_g, flat_g = np.meshgrid(flon, flat)
    pts = np.stack([flat_g.ravel(), flon_g.ravel()], axis=-1)
    coarse_at_fine = coarse_at_fine_interp(pts).reshape(fine.shape)

    # Dividing by a coarse value that's nonzero but tiny (e.g. GeoTIFF
    # round-trip precision noise near a cell's true zero) blows S up by
    # orders of magnitude for a handful of cells. Treat anything below 1%
    # of the domain's typical nonzero coarse value as "effectively zero"
    # and let normalized_conv_fill() interpolate S there instead.
    nonzero_coarse = coarse[coarse > 0]
    eps = 0.01 * np.median(nonzero_coarse)
    with np.errstate(invalid="ignore", divide="ignore"):
        S = fine / coarse_at_fine
    S[coarse_at_fine <= eps] = np.nan
    S[~np.isfinite(fine)] = np.nan
    # safety net: clip remaining extreme outliers to the 99.5th percentile
    s_hi = np.nanpercentile(S, 99.5)
    S = np.clip(S, None, s_hi)

    # ---- step 3: smooth F_coarse on the coarse grid, then upsample --------
    coarse_smoothed = gaussian_filter(coarse, sigma=COARSE_SMOOTH_SIGMA_CELLS)
    smooth_interp = RegularGridInterpolator(
        (clat, clon), coarse_smoothed, method="linear", bounds_error=False, fill_value=0.0
    )
    coarse_smoothed_at_fine = smooth_interp(pts).reshape(fine.shape)

    # ---- step 4: fill S into cells that gained harvest from smoothing -----
    S_filled = normalized_conv_fill(S, sigma=TEXTURE_FILL_SIGMA_FINE_CELLS)
    S_filled = np.nan_to_num(S_filled, nan=1.0)  # remaining gaps: no info, use flat

    # ---- step 5: new field --------------------------------------------
    new_field = coarse_smoothed_at_fine * S_filled
    new_field[~np.isfinite(fine)] = np.nan  # keep same land/ocean mask as original

    print(f"Original downscaled  : mean={np.nanmean(fine):.5f}  max={np.nanmax(fine):.5f}  sum={np.nansum(fine):.2f}")
    print(f"Smoothed-then-downsc.: mean={np.nanmean(new_field):.5f}  max={np.nanmax(new_field):.5f}  sum={np.nansum(new_field):.2f}")
    print(f"Coarse total (0.25deg): sum={np.nansum(coarse):.2f}   coarse-smoothed sum={np.nansum(coarse_smoothed):.2f}")

    # ---- plot: original vs smoothed-input result --------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), subplot_kw={"projection": ccrs.PlateCarree()})

    def panel(ax, arr, lat, lon, title, norm):
        mesh = ax.pcolormesh(lon, lat, arr, cmap="OrRd", norm=norm, shading="auto",
                             transform=ccrs.PlateCarree())
        ax.coastlines(resolution="10m", linewidth=0.8)
        ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor="black")
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())
        ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.5, linestyle="--")
        ax.set_title(title)
        return mesh

    mesh1 = panel(axes[0], fine, flat, flon,
                  f"Current: downscaled from raw 0.25° F_coarse ({YEAR})",
                  quantile_boundary_norm(fine))
    fig.colorbar(mesh1, ax=axes[0], label="Harvest (unitless)", orientation="horizontal", pad=0.05, shrink=0.9)

    mesh2 = panel(axes[1], new_field, flat, flon,
                  f"Option 1: downscaled from SMOOTHED F_coarse ({YEAR})",
                  quantile_boundary_norm(new_field))
    fig.colorbar(mesh2, ax=axes[1], label="Harvest (unitless)", orientation="horizontal", pad=0.05, shrink=0.9)

    out_path = os.path.join(OUT_DIR, f"Option1_SmoothCoarse_vs_Current_{YEAR}.png")
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
