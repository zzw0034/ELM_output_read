"""
End-of-century (2091-2100 mean) GPP maps for the SSP3-7.0 management
scenarios of the PRE-rerun 4km case family (20260908_seus_4km_fut_*):
Default, RF (reforestation), DF (deforestation counterfactual), RH
(reduced harvest). SSP3-7.0 is the only SSP that has management variants
in this older family -- the other three SSPs only got RF/DF/RH in the
2026-09-15 batch of the newer 20260910_seus_rerun family.

IMPORTANT path note: this family's run output is NO LONGER on scratch.
It was moved to durable project storage at
  /projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260901_before_seus_rerun/
so this module's CASE_ROOT below differs from the (now stale)
CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs" still sitting in
this folder's common.py. Fix common.py before reusing the other scripts
in this folder.

Must run via Slurm (sbatch), never on the login node -- reads 40 h0 files
(~12 GB each).
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

CASE_ROOT = "/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260901_before_seus_rerun"
OUTDIR = "/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/outputs"

CASES = [
    ("SSP3-7.0 Default", "20260908_seus_4km_fut_ssp370"),
    ("SSP3-7.0 RF (reforest)", "20260908_seus_4km_fut_ssp370_RF"),
    ("SSP3-7.0 DF (deforest counterfactual)", "20260908_seus_4km_fut_ssp370_DF"),
    ("SSP3-7.0 RH (reduced harvest)", "20260908_seus_4km_fut_ssp370_RH"),
]

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
    os.makedirs(OUTDIR, exist_ok=True)
    maps = {}
    lon = lat = None
    for label, case in CASES:
        print(f"loading {label} ({case})...", flush=True)
        lon, lat, m = load_gpp_mean(case)
        maps[label] = m
        print(f"  mean={np.nanmean(m):.1f} range=[{np.nanmin(m):.1f}, {np.nanmax(m):.1f}]")

    vmin = float(np.nanmin([np.nanmin(m) for m in maps.values()]))
    vmax = float(np.nanmax([np.nanmax(m) for m in maps.values()]))
    print(f"shared color scale: [{vmin:.1f}, {vmax:.1f}]")

    fig, axes = plt.subplots(2, 2, figsize=(15, 11),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    for ax, (label, _case) in zip(axes.flat, CASES):
        ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.4)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
        ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())
        pc = ax.pcolormesh(lon, lat, maps[label], transform=ccrs.PlateCarree(),
                           cmap="viridis", vmin=vmin, vmax=vmax, shading="auto")
        ax.set_title(label, fontsize=11)

    fig.colorbar(pc, ax=list(axes.flat), orientation="horizontal", pad=0.04, shrink=0.5,
                 label="GPP (gC m$^{-2}$ yr$^{-1}$)")
    fig.suptitle("SEUS 4km pre-rerun family: SSP3-7.0 management scenarios, "
                 "end-of-century GPP (2091-2100 mean)", fontsize=14)
    out = os.path.join(OUTDIR, "gpp_ssp370_mgmt_2091_2100_prererun.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
