"""
Diagnostic figure linking the DF-scenario GPP discontinuity seen in
gpp_management_scenarios_2091_2100.png (SSP5-8.5 DF panel, ~lat 30.8-30.9N
near the AL/FL Gulf coast) to its root cause: DF's grass-routing weight
w_k(g) = p(g,k,2023)/grass_2023(g) becomes numerically unstable wherever
grass_2023(g) (pre-existing 2023 grass fraction) is very small -- a handful
of near-pure-forest cells right at this latitude have grass_2023 < 2%,
making w_k (and therefore DF's post-clearing C3/C4 grass mix) swing wildly
between adjacent 4km cells. See ELM_Futu_landuseInput/future_runs/docs/
BLOCKER_pct_nat_pft_sum.md investigation log (2026-09-21) for the full
derivation, including why this is NOT the drawn state-border line (verified
by re-plotting with zero map overlays -- the jump persists) and NOT the
same discontinuity codex checked at 30.98-31.02N (that's ~0.15-0.2 deg
north of the actual jump row, which is why that check found continuity).

Four panels:
  A. DF GPP 2091-2100, zoomed, with the jump latitude marked
  B. grass_2023(%) from the Default landuse file, same region -- shows the
     low-grass patch whose location matches panel A's jump
  C. Full-domain-width row transect: Default vs DF GPP per row, with the
     anomalous DF-only jump highlighted
  D. w14 (C4-of-2023-grass weight) map, same region -- shows the noisy/
     unstable weight field wherever grass_2023 is small

Must run via Slurm, not the login node. Reads full h0/landuse files.
"""
import os
import glob
import re

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from common import OUTDIR_ROOT

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
DEFAULT_CASE = "20260917_seus_4km_fut_ssp585"
DF_CASE = "20260915_seus_4km_fut_ssp585_DF"
DEFAULT_LANDUSE = ("/projects/hpcl-cli185/proj-shared/zw5/ELM_Futu_landuseInput/outputs/"
                    "processed/landuse.timeseries_SEUS_1_24deg_nlcd2elm_SSP5_RCP85_simyr2024-2100.nc")

JUMP_LAT_RANGE = (30.81, 30.85)  # the identified DF-specific discontinuity


def _year_of(f):
    return int(re.search(r"\.h0\.(\d+)-", f).group(1))


def load_gpp_mean(case, year_min=2091, year_max=2100):
    d = os.path.join(CASE_ROOT, case, "run")
    files = sorted(f for f in glob.glob(os.path.join(d, f"{case}.elm.h0.*.nc"))
                   if not f.endswith(".loc") and year_min <= _year_of(f) <= year_max)
    stack = []
    lat = lon = None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values
        vals = ds["GPP"].values
        dt = tb[:, 1] - tb[:, 0]
        w = dt / dt.sum()
        m = np.nansum(vals * w[:, None, None], axis=0) * 365 * 86400.0
        stack.append(m)
        if lat is None:
            lat = ds["lat"].values
            lon = ds["lon"].values
        ds.close()
    return lon, lat, np.nanmean(np.stack(stack), axis=0)


def main():
    print("Loading Default and DF GPP (2091-2100 mean)...")
    lon, lat, gpp_def = load_gpp_mean(DEFAULT_CASE)
    _, _, gpp_df = load_gpp_mean(DF_CASE)

    print("Loading grass_2023 / w14 from the Default landuse file...")
    ds = xr.open_dataset(DEFAULT_LANDUSE, decode_times=False)
    lat2d = np.asarray(ds["LATIXY"][:])
    lon2d = np.asarray(ds["LONGXY"][:])
    mask = np.asarray(ds["PFTDATA_MASK"][:]) == 1
    pft2023 = np.asarray(ds["PCT_NAT_PFT"][0])
    GRASS = [12, 13, 14]
    grass2023 = pft2023[GRASS].sum(axis=0)
    eps = 1e-9
    w14 = pft2023[14] / np.where(grass2023 > eps, grass2023, np.nan)
    w14 = np.where(mask, w14, np.nan)
    grass2023_masked = np.where(mask, grass2023, np.nan)
    ds.close()

    # --- Panel C data: full-domain-width row transect ---
    print("Computing full-domain-width row transect...")
    rows, lats, def_means, df_means = [], [], [], []
    for i in range(140, 200):
        row_d = gpp_def[i]
        row_f = gpp_df[i]
        valid = np.isfinite(row_d) & (row_d > 10)
        if valid.sum() < 5:
            continue
        latval = lat[i, valid].mean() if lat.ndim == 2 else lat[i]
        rows.append(i)
        lats.append(latval)
        def_means.append(np.nanmean(row_d[valid]))
        df_means.append(np.nanmean(row_f[valid]))
    lats = np.array(lats); def_means = np.array(def_means); df_means = np.array(df_means)

    # --- Figure ---
    fig = plt.figure(figsize=(16, 14))
    extent = [-90, -83, 29, 34]

    ax_a = fig.add_subplot(2, 2, 1, projection=ccrs.PlateCarree())
    ax_a.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax_a.set_extent(extent, crs=ccrs.PlateCarree())
    pc = ax_a.pcolormesh(lon, lat, gpp_df, transform=ccrs.PlateCarree(), cmap="viridis", shading="auto")
    ax_a.plot(extent[:2], [np.mean(JUMP_LAT_RANGE)] * 2, color="red", linewidth=1.2,
              linestyle="--", transform=ccrs.PlateCarree())
    ax_a.set_title("A. DF GPP 2091-2100 mean\n(red dashed = identified jump latitude, ~30.83N)")
    fig.colorbar(pc, ax=ax_a, shrink=0.7, label="GPP (gC m$^{-2}$ yr$^{-1}$)")

    ax_b = fig.add_subplot(2, 2, 2, projection=ccrs.PlateCarree())
    ax_b.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax_b.set_extent(extent, crs=ccrs.PlateCarree())
    pc2 = ax_b.pcolormesh(lon2d, lat2d, grass2023_masked, transform=ccrs.PlateCarree(),
                           cmap="YlOrRd_r", vmin=0, vmax=10, shading="auto")
    ax_b.plot(extent[:2], [np.mean(JUMP_LAT_RANGE)] * 2, color="blue", linewidth=1.2,
              linestyle="--", transform=ccrs.PlateCarree())
    ax_b.set_title("B. grass_2023 (%, capped at 10%) -- source of w_k's unstable denominator\n"
                    "(dark red = almost no pre-existing grass; blue dashed = same jump latitude)")
    fig.colorbar(pc2, ax=ax_b, shrink=0.7, label="grass_2023 (%)")

    ax_c = fig.add_subplot(2, 2, 3)
    ax_c.plot(lats, def_means, "o-", color="tab:blue", label="Default", markersize=3)
    ax_c.plot(lats, df_means, "o-", color="tab:orange", label="DF", markersize=3)
    ax_c.axvspan(*JUMP_LAT_RANGE, color="red", alpha=0.2, label="identified DF-only jump")
    ax_c.set_xlabel("Latitude (deg N)")
    ax_c.set_ylabel("Row-mean GPP (gC m$^{-2}$ yr$^{-1}$)")
    ax_c.set_title("C. Full-domain-width row transect, Default vs DF\n"
                    "(DF drops ~338 at the jump row; Default drops only ~24 at the same row)")
    ax_c.legend()
    ax_c.grid(alpha=0.3)

    ax_d = fig.add_subplot(2, 2, 4, projection=ccrs.PlateCarree())
    ax_d.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax_d.set_extent(extent, crs=ccrs.PlateCarree())
    pc4 = ax_d.pcolormesh(lon2d, lat2d, w14, transform=ccrs.PlateCarree(),
                           cmap="RdBu_r", vmin=0, vmax=0.3, shading="auto")
    ax_d.plot(extent[:2], [np.mean(JUMP_LAT_RANGE)] * 2, color="black", linewidth=1.2,
              linestyle="--", transform=ccrs.PlateCarree())
    ax_d.set_title("D. w14 = C4_2023 / grass_2023 (DF's local routing weight)\n"
                    "noisy/patchy wherever panel B is dark red")
    fig.colorbar(pc4, ax=ax_d, shrink=0.7, label="w14 (fraction)")

    fig.suptitle("Why DF shows a GPP discontinuity near 30.83N: low grass_2023 destabilizes w_k(g)",
                 fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    outpath = os.path.join(OUTDIR_ROOT, "diagnose_df_gpp_line_31N.png")
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    print(f"wrote {outpath}")


if __name__ == "__main__":
    main()
