"""
Large single-panel GPP maps of the 4 km SSP5-8.5 DF run at crit_dayl_stress =
38000 s (20260922_seus_4km_fut_ssp585_DF_cds38000), 2091-2100 mean, drawn with
NO overlays at all -- no threshold line, coastlines or state borders -- so that
nothing on the plot can hide (or fake) an east-west line at 30.833N.

Outputs (outputs/):
  map_newDF_ssp585_gpp_annual_nooverlay.png   whole domain, annual GPP
  map_newDF_ssp585_gpp_jan_nooverlay.png      whole domain, January GPP
  map_newDF_ssp585_gpp_annual_zoom_nooverlay.png
      annual GPP, 28.8-32.8N only (the old threshold is at 30.833N; the range
      is stated in the axis limits, not drawn)

Reuses the verified readers in analyze_4km_cds38000.py (day-weighted annual
mean from time_bounds, mcdate year check). Run through Slurm:
  sbatch -J newDF_map submit_py.sbatch plot_newDF_gpp_nooverlay.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze_4km_cds38000 import OUTDIR, PERIODS, LATE, JAN, case_name, h0_climatology, load_grid

SSP = "ssp585"
RUN = "newDF"
ZOOM_LAT = (28.8, 32.8)


def draw(lon, lat, fld, title, fname, vmax, ylim=None):
    fig, ax = plt.subplots(figsize=(15, 10) if ylim is None else (15, 6))
    pc = ax.pcolormesh(lon, lat, fld, cmap="viridis", vmin=0, vmax=vmax, shading="auto")
    ax.set_aspect("equal")
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title(title, fontsize=13)
    fig.colorbar(pc, ax=ax, shrink=0.8, label="GPP (gC m$^{-2}$ yr$^{-1}$)")
    fig.tight_layout()
    out = os.path.join(OUTDIR, fname)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    land = W > 0
    case = case_name(RUN, SSP)
    print(f"reading {case}, {LATE}", flush=True)
    ann, mon = h0_climatology(case, "GPP", PERIODS[LATE])
    ann = np.where(land, ann, np.nan)
    jan = np.where(land, mon[JAN], np.nan)
    tag = f"{case}, {LATE} mean, crit_dayl_stress = 38000 s"
    draw(lon, lat, ann, f"Annual GPP -- {tag}",
         f"map_newDF_{SSP}_gpp_annual_nooverlay.png", np.nanpercentile(ann, 99.5))
    draw(lon, lat, jan, f"January GPP (annualised rate) -- {tag}",
         f"map_newDF_{SSP}_gpp_jan_nooverlay.png", np.nanpercentile(jan, 99.5))
    band = (lat >= ZOOM_LAT[0]) & (lat <= ZOOM_LAT[1])
    draw(lon, lat, ann, f"Annual GPP, {ZOOM_LAT[0]}-{ZOOM_LAT[1]}N -- {tag}",
         f"map_newDF_{SSP}_gpp_annual_zoom_nooverlay.png",
         np.nanpercentile(ann[band], 99.5), ylim=ZOOM_LAT)


if __name__ == "__main__":
    main()
