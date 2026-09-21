"""
End-of-century (2091-2100 mean) GPP spatial maps for the full 4 SSP x 3
management-scenario matrix of 4km SEUS runs -- 12 panels, one shared color
scale so every panel is directly comparable.

Rows    = management scenario: RF (reforestation), DF (deforestation
          counterfactual), RH (reduced harvest)
Columns = SSP1-1.9, SSP2-4.5, SSP3-7.0, SSP5-8.5

Note the case-name prefixes differ by SSP: the SSP3-7.0 management cases
were built 2026-09-17 as part of the original 7 production cases, while
SSP1-1.9 / SSP2-4.5 / SSP5-8.5 management cases were built 2026-09-15
(and the DF/RH ones among those were the 6 that had to be rerun after the
PCT_NAT_PFT landuse fix -- see BLOCKER_pct_nat_pft_sum.md).

RF caveat worth remembering when reading the figure: RF uses ONE shared,
scenario-independent landuse file, so RF panels differ between SSPs only
through climate forcing, not through their land-cover trajectory.

Must run via Slurm (sbatch), never on the login node -- reads 120 h0 files
(~12 GB each).
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

SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
MGMT = ["RF", "DF", "RH"]

CASES = {
    ("SSP1-1.9", "RF"): "20260915_seus_4km_fut_ssp119_RF",
    ("SSP1-1.9", "DF"): "20260915_seus_4km_fut_ssp119_DF",
    ("SSP1-1.9", "RH"): "20260915_seus_4km_fut_ssp119_RH",
    ("SSP2-4.5", "RF"): "20260915_seus_4km_fut_ssp245_RF",
    ("SSP2-4.5", "DF"): "20260915_seus_4km_fut_ssp245_DF",
    ("SSP2-4.5", "RH"): "20260915_seus_4km_fut_ssp245_RH",
    ("SSP3-7.0", "RF"): "20260917_seus_4km_fut_ssp370_RF",
    ("SSP3-7.0", "DF"): "20260917_seus_4km_fut_ssp370_DF",
    ("SSP3-7.0", "RH"): "20260917_seus_4km_fut_ssp370_RH",
    ("SSP5-8.5", "RF"): "20260915_seus_4km_fut_ssp585_RF",
    ("SSP5-8.5", "DF"): "20260915_seus_4km_fut_ssp585_DF",
    ("SSP5-8.5", "RH"): "20260915_seus_4km_fut_ssp585_RH",
}

YEAR_MIN, YEAR_MAX = 2091, 2100
SEC_PER_YEAR_NOLEAP = 365 * 86400.0


def _year_of(f):
    return int(re.search(r"\.h0\.(\d+)-", f).group(1))


def load_gpp_mean(case):
    d = os.path.join(CASE_ROOT, case, "run")
    files = sorted(f for f in glob.glob(os.path.join(d, f"{case}.elm.h0.*.nc"))
                   if not f.endswith(".loc") and YEAR_MIN <= _year_of(f) <= YEAR_MAX)
    if not files:
        raise ValueError(f"no h0 files for {case} in [{YEAR_MIN},{YEAR_MAX}]")
    stack = []
    lat = lon = None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values
        vals = ds["GPP"].values
        dt = tb[:, 1] - tb[:, 0]
        w = dt / dt.sum()
        m = np.nansum(vals * w[:, None, None], axis=0) * SEC_PER_YEAR_NOLEAP
        stack.append(m)
        if lat is None:
            lat = ds["lat"].values
            lon = ds["lon"].values
        ds.close()
    return lon, lat, np.nanmean(np.stack(stack, axis=0), axis=0)


def main():
    maps = {}
    lon = lat = None
    for mg in MGMT:
        for ssp in SSPS:
            case = CASES[(ssp, mg)]
            print(f"loading {ssp} {mg} ({case})...", flush=True)
            lon, lat, m = load_gpp_mean(case)
            maps[(ssp, mg)] = m
            print(f"  mean={np.nanmean(m):.1f} range=[{np.nanmin(m):.1f}, {np.nanmax(m):.1f}]")

    vmin = float(np.nanmin([np.nanmin(m) for m in maps.values()]))
    vmax = float(np.nanmax([np.nanmax(m) for m in maps.values()]))
    print(f"shared color scale: [{vmin:.1f}, {vmax:.1f}]")

    fig, axes = plt.subplots(len(MGMT), len(SSPS), figsize=(22, 13),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    for i, mg in enumerate(MGMT):
        for j, ssp in enumerate(SSPS):
            ax = axes[i, j]
            ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.4)
            ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
            ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())
            pc = ax.pcolormesh(lon, lat, maps[(ssp, mg)], transform=ccrs.PlateCarree(),
                               cmap="viridis", vmin=vmin, vmax=vmax, shading="auto")
            ax.set_title(f"{ssp}  {mg}", fontsize=11)

    fig.colorbar(pc, ax=list(axes.flat), orientation="horizontal", pad=0.04, shrink=0.4,
                 label="GPP (gC m$^{-2}$ yr$^{-1}$)")
    fig.suptitle("SEUS 4km: end-of-century GPP (2091-2100 mean), 4 SSPs x 3 management scenarios",
                 fontsize=15)
    out = os.path.join(OUTDIR_ROOT, "gpp_4ssp_3mgmt_2091_2100.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
