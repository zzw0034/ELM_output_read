"""Map of the SEUS 4km (1/24deg) simulation domain used by the
20260915_seus_4km_fut_management_scenarios case set (and the rest of the
20260910_seus_rerun 4km cases, which all share the same domain file).

Shows the active land-model grid cells (domain mask == 1) plus US state
boundaries, so the true simulated footprint (not just the nominal lon/lat
bounding box) is visible. See seus_4km_grid_and_boundary memory: the grid is
nominally lon -95..-74, lat 24..37.5, but rows south of ~25N have zero active
land cells.

Reads only the domain file (~16 MB), so this runs fine on the login node --
does not need Slurm, unlike the h0-file scripts in this folder.
"""
import os

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

DOMAIN_FILE = "/projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/domain.lnd.SEUS_1_24deg.nc"
OUTDIR_ROOT = ("/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/"
               "20260915_seus_4km_fut_management_scenarios/figure")


def main():
    os.makedirs(OUTDIR_ROOT, exist_ok=True)
    ds = xr.open_dataset(DOMAIN_FILE)
    lon = ds["xc"].values
    lat = ds["yc"].values
    mask = ds["mask"].values.astype(float)
    ds.close()

    n_active = int((mask == 1).sum())
    lon_min, lon_max = lon.min(), lon.max()
    lat_min, lat_max = lat.min(), lat.max()

    mask_plot = np.where(mask == 1, 1.0, np.nan)

    fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    ax.set_extent([-96, -73, 23, 39], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="black", linewidth=0.6)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.8)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.8)

    ax.pcolormesh(lon, lat, mask_plot, transform=ccrs.PlateCarree(),
                  cmap=matplotlib.colors.ListedColormap(["#2b8cbe"]), shading="auto",
                  alpha=0.7)

    nominal_box = plt.Rectangle((lon_min, lat_min), lon_max - lon_min, lat_max - lat_min,
                                 fill=False, edgecolor="red", linewidth=1.5, linestyle="--",
                                 transform=ccrs.PlateCarree(), label="nominal grid bbox")
    ax.add_patch(nominal_box)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="gray", alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    ax.set_title(
        f"SEUS 4km (1/24deg) simulation domain\n"
        f"grid {mask.shape[1]}x{mask.shape[0]}, nominal bbox lon [{lon_min:.2f}, {lon_max:.2f}] "
        f"lat [{lat_min:.2f}, {lat_max:.2f}], {n_active} active land cells",
        fontsize=11,
    )
    ax.legend(loc="lower left", fontsize=8)

    outfile = os.path.join(OUTDIR_ROOT, "domain_map.png")
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"active land cells: {n_active} / {mask.size}")
    print(f"lon range: [{lon_min:.4f}, {lon_max:.4f}]  lat range: [{lat_min:.4f}, {lat_max:.4f}]")
    print(f"wrote {outfile}")


if __name__ == "__main__":
    main()
