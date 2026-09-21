"""
Winter (January) vs summer (July) GPP maps showing the crit_dayl_stress
phenology threshold artifact at 30.833N.

ELM's stress-deciduous phenology (all grass PFTs) force-triggers leaf
offset whenever daylength <= crit_dayl_stress. This project's parameter
file (clm_params_SEUS_c260712.nc) sets crit_dayl_stress = 36000 s = 10.0
hours -- NOT the 6 hours the source comment in PhenologyMod.F90 claims.
Winter-solstice daylength equals 10.0 hours at exactly 30.833N, so south
of that line grass never goes dormant and north of it grass is forced
dormant every winter.

The figure makes the mechanism visible and falsifiable in one look:
  - JANUARY: a hard GPP step at 30.833N, ~4x stronger in DF (which is
    ~100% grass after clearing) than in Default (~15-20% grass).
  - JULY: daylength is above the threshold everywhere, so the step
    essentially vanishes -- this is the control that rules out any
    static input-data artifact (soil, landuse, climate all checked
    separately and found smooth).

Full write-up: ../../../CRIT_DAYL_STRESS_ARTIFACT.md

Must run via Slurm (sbatch), never on the login node.
"""
import glob
import os
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

THRESHOLD_LAT = 30.833  # where winter-solstice daylength == 36000 s == 10.0 hr
SEC_PER_YEAR_NOLEAP = 365 * 86400.0
YEAR_MIN, YEAR_MAX = 2091, 2100
EXTENT = [-92, -75, 24, 37]


def _year_of(f):
    return int(re.search(r"\.h0\.(\d+)-", f).group(1))


def load_month_mean(case, month_idx):
    """Multi-year mean of one calendar month (0=Jan, 6=Jul), as an
    annualized rate (gC/m2/yr) so the numbers are comparable to the
    annual-mean figures elsewhere in this folder."""
    d = os.path.join(CASE_ROOT, case, "run")
    files = sorted(f for f in glob.glob(os.path.join(d, f"{case}.elm.h0.*.nc"))
                   if not f.endswith(".loc") and YEAR_MIN <= _year_of(f) <= YEAR_MAX)
    stack = []
    lat = lon = None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        stack.append(ds["GPP"].values[month_idx] * SEC_PER_YEAR_NOLEAP)
        if lat is None:
            lat = ds["lat"].values
            lon = ds["lon"].values
        ds.close()
    return lon, lat, np.nanmean(np.stack(stack, axis=0), axis=0)


def main():
    panels = {}
    lon = lat = None
    for month_idx, mname in [(0, "January"), (6, "July")]:
        for label, case in [("Default", DEFAULT_CASE), ("DF", DF_CASE)]:
            print(f"loading {mname} {label}...", flush=True)
            lon, lat, m = load_month_mean(case, month_idx)
            panels[(mname, label)] = m
            print(f"  mean={np.nanmean(m):.1f}")

    fig, axes = plt.subplots(2, 2, figsize=(17, 12),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    for i, mname in enumerate(["January", "July"]):
        # one color scale per row: winter and summer magnitudes differ ~3x,
        # but Default vs DF must stay directly comparable within a row
        row_vals = [panels[(mname, lab)] for lab in ("Default", "DF")]
        vmin = float(np.nanmin([np.nanmin(v) for v in row_vals]))
        vmax = float(np.nanmax([np.nanmax(v) for v in row_vals]))
        for j, lab in enumerate(["Default", "DF"]):
            ax = axes[i, j]
            ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
            ax.set_extent(EXTENT, crs=ccrs.PlateCarree())
            pc = ax.pcolormesh(lon, lat, panels[(mname, lab)],
                               transform=ccrs.PlateCarree(), cmap="viridis",
                               vmin=vmin, vmax=vmax, shading="auto")
            ax.plot(EXTENT[:2], [THRESHOLD_LAT] * 2, color="red", linewidth=1.0,
                    linestyle="--", transform=ccrs.PlateCarree())
            ax.set_title(f"{mname} — {lab}", fontsize=12)
        fig.colorbar(pc, ax=list(axes[i, :]), orientation="vertical", pad=0.02,
                     shrink=0.85, label=f"{mname} GPP (gC m$^{{-2}}$ yr$^{{-1}}$)")

    fig.suptitle("crit_dayl_stress = 36000 s (10 hr) artifact: grass is force-dormant north of "
                 f"{THRESHOLD_LAT}N (red dashed)\n"
                 "January shows a hard step (strongest in DF, ~100% grass); July does not — "
                 "daylength is above threshold everywhere in summer",
                 fontsize=13)
    out = os.path.join(OUTDIR_ROOT, "gpp_jan_vs_jul_daylength_artifact.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
