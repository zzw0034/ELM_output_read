# 20260902 Southeast hires, smoothed harvest — every-20-years QC maps

Case: `20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC`
Run directory: `/scratch/hpcl-cli185/zw5/cime_output_dirs/<case>/run` (1850–2023)
Forcing: `landuse.timeseries_SEUS_1_24deg_nlcd2elm_smoothHARV_simyr1850-2023_c260723.nc`

## Why

`analyses/20260723_..._harvfix_.../outputs/Biomass_2010.png` showed rectangular
patches. `AnnualHarvest_2010.png` from the same analysis showed the same
rectangles, which identified the cause: LUH2 wood harvest is native 0.25°, and
harvfix's area-conservative downscaling to 4 km leaves each coarse cell uniform,
so decades of accumulated harvest imprint a 0.25° checkerboard on the biomass
pool. The forcing was smoothed and the historical simulation rerun. This
analysis checks whether the blocks are gone.

## What gets produced

Five variables, every 20 years from 1850 through 2010, plus 2023 (the run's last
full year, added so the series also shows the end state):

| Variable | Source | Units |
|---|---|---|
| Aboveground biomass | `TOTVEGC_ABG`, annual mean | kgC/m² |
| Annual wood harvest | `HARVEST_VH1+VH2+SH1+SH2+SH3` from the smoothed forcing | unitless |
| GPP | annual total, day-weighted | gC/m²/year |
| NPP | annual total, day-weighted | gC/m²/year |
| Soil organic C, 0–30 cm | `SOIL1–4C_vr` integrated to 0.30 m, December snapshot | kgC/m² |

## How to run

Two stages, because the Pathfinder conda env has no cartopy.

1. **On Pathfinder** — extract from the 12 GB/year h0 files, write GeoTIFFs and
   quick-look PNGs:

   ```bash
   sbatch --export=NONE run_extract_20yr_maps.slurm
   ```

2. **Locally** — pull `outputs/` back (`remote -> local`), then re-plot the
   GeoTIFFs with state boundaries:

   ```bash
   /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_20yr_maps_local.py
   /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python plot_before_after_blockiness_local.py
   ```

`plot_20yr_maps_local.py` writes each year twice: `<Var>_<year>.png` on one
shared quantile scale built from all years pooled, so the series reads as a time
evolution, and `<Var>_selfscaled_<year>.png` on a per-year scale, which is what
the 20260723 figures used and is the strictest look at residual block structure.

`plot_before_after_blockiness_local.py` puts the old and new 2010 fields side by
side with their difference, and reports a blockiness ratio: the mean absolute
step across cell edges that fall on a 0.25° boundary, divided by the mean
absolute step across every other cell edge. A ratio near 1 means the field no
longer jumps preferentially at coarse-grid boundaries.

`outputs/` is git-ignored. The remote root is Lustre scratch and is purgeable,
so nothing there is a backup.
