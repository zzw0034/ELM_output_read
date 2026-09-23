"""
Large GPP maps of the 4 km SSP5-8.5 DF runs, 2091-2100 mean, drawn with NO
overlays at all -- no threshold line, coastlines or state borders -- so that
nothing on the plot can hide (or fake) an east-west line at 30.833N.

  oldDF  20260915_seus_4km_fut_ssp585_DF           crit_dayl_stress = 36000 s
  newDF  20260922_seus_4km_fut_ssp585_DF_cds38000  crit_dayl_stress = 38000 s

Outputs (outputs/), for each run <r> in {oldDF, newDF}, each on its own colour
scale (99.5th percentile of that field):
  map_<r>_ssp585_gpp_annual_nooverlay.png       whole domain, annual GPP
  map_<r>_ssp585_gpp_jan_nooverlay.png          whole domain, January GPP
  map_<r>_ssp585_gpp_annual_zoom_nooverlay.png  annual GPP, 28.8-32.8N only
and side by side, old | new on ONE shared colour scale:
  compare_oldDF_newDF_ssp585_gpp_{annual,annual_zoom,jan}_nooverlay.png
The zoom range is stated in the axis limits, not drawn.

Reuses the verified readers in analyze_4km_cds38000.py (day-weighted annual
mean from time_bounds, mcdate year check). Run through Slurm:
  sbatch -J DF_maps submit_py.sbatch plot_newDF_gpp_nooverlay.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze_4km_cds38000 import OUTDIR, PERIODS, LATE, JAN, case_name, h0_climatology, load_grid

SSP = "ssp585"
RUNS = {"oldDF": 36000, "newDF": 38000}
ZOOM_LAT = (28.8, 32.8)
KINDS = {  # kind -> (field key, ylim, label)
    "annual": ("ann", None, "Annual GPP"),
    "annual_zoom": ("ann", ZOOM_LAT, f"Annual GPP, {ZOOM_LAT[0]}-{ZOOM_LAT[1]}N"),
    "jan": ("jan", None, "January GPP (annualised rate)"),
}


def vmax_of(fld, lat, ylim):
    if ylim is not None:
        fld = fld[(lat >= ylim[0]) & (lat <= ylim[1])]
    return np.nanpercentile(fld, 99.5)


def panel(ax, lon, lat, fld, vmax, ylim, title):
    pc = ax.pcolormesh(lon, lat, fld, cmap="viridis", vmin=0, vmax=vmax, shading="auto")
    ax.set_aspect("equal")
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title(title, fontsize=12)
    return pc


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    land = W > 0
    fields = {}
    for run in RUNS:
        case = case_name(run, SSP)
        print(f"reading {case}, {LATE}", flush=True)
        ann, mon = h0_climatology(case, "GPP", PERIODS[LATE])
        fields[run] = {"ann": np.where(land, ann, np.nan), "jan": np.where(land, mon[JAN], np.nan)}
        del mon

    for kind, (key, ylim, label) in KINDS.items():
        size = (15, 10) if ylim is None else (15, 6)
        # one run per figure, own colour scale
        for run, cds in RUNS.items():
            fld = fields[run][key]
            fig, ax = plt.subplots(figsize=size)
            pc = panel(ax, lon, lat, fld, vmax_of(fld, lat, ylim), ylim,
                       f"{label} -- {case_name(run, SSP)}, {LATE} mean, crit_dayl_stress = {cds} s")
            fig.colorbar(pc, ax=ax, shrink=0.8, label="GPP (gC m$^{-2}$ yr$^{-1}$)")
            fig.tight_layout()
            out = os.path.join(OUTDIR, f"map_{run}_{SSP}_gpp_{kind}_nooverlay.png")
            fig.savefig(out, dpi=200)
            plt.close(fig)
            print(f"wrote {out}")
        # old | new side by side, shared colour scale
        vmax = max(vmax_of(fields[r][key], lat, ylim) for r in RUNS)
        fig, axes = plt.subplots(1, 2, figsize=(26, 9) if ylim is None else (26, 5.5))
        for ax, (run, cds) in zip(axes, RUNS.items()):
            pc = panel(ax, lon, lat, fields[run][key], vmax, ylim,
                       f"{run}: crit_dayl_stress = {cds} s")
        fig.colorbar(pc, ax=list(axes), shrink=0.8, label="GPP (gC m$^{-2}$ yr$^{-1}$)")
        fig.suptitle(f"4 km {SSP} DF, {label}, {LATE} mean (shared colour scale, no overlays)",
                     fontsize=14)
        out = os.path.join(OUTDIR, f"compare_oldDF_newDF_{SSP}_gpp_{kind}_nooverlay.png")
        fig.savefig(out, dpi=170, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
