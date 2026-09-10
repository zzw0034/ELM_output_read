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

## Finding (job 522178, 2026-09-09)

**The rectangles in Biomass_2010 are gone.** `BiomassBeforeAfterZoom_2010.png`
is the clearest evidence: over Mississippi/Alabama/Georgia the old run shows
hard-edged plateaus snapped to the drawn 0.25° gridlines, and the new run shows
organic texture with no rectangles. The after-minus-before panel is itself made
of 0.25° blocks, up to about ±1.5 kgC/m², so the change is exactly the block
pattern being removed rather than a general shift. Domain-wide, biomass differs
between the two runs by 4.8% of its mean.

A residual coarse-grid imprint remains, and it starts in the forcing. Block
index over the zoom box, where 1850 biomass sits at 0.93 because the surface
dataset carries a little 6-cell structure of its own:

| Field | harvfix | harvfixsmooth |
|---|---|---|
| Annual wood harvest 2010 | 2.375 | 1.748 |
| Biomass 2010 | 1.193 | 1.124 |
| Biomass 1850 (baseline, identical in both runs) | 0.932 | 0.932 |

So smoothing removed roughly a quarter of the biomass field's excess over
baseline, and the harvest forcing still jumps preferentially on the 0.25° grid.
`AnnualHarvestBeforeAfterZoom_2010.png` shows why: the smoothed forcing no
longer has single-cell rectangles, but it still holds coarse plateaus. If the
remaining imprint matters, the next lever is the forcing, not the model.

Read the domain-wide column of `blockiness_metric_2010.txt` with care. The
index is decisive for the forcing, whose blocks cover the whole domain, and
only weakly sensitive for biomass, whose blocks cover a fraction of it and
compete with genuine 4 km heterogeneity in the same step statistics. The
domain-wide biomass index barely moves (1.030 → 1.034) even though the zoom
box and the figures both show a clear improvement.

**A separate and larger problem surfaced from these same figures.** The pale
areas in Georgia and Florida are not missing data and not a colour artifact. The
needleleaf evergreen temperate PFT sits at exactly zero leaf carbon on 9% of its
patches here and 78% at 0.5 degrees, permanently, while every deciduous PFT in
the same gridcells is healthy. Florida's biomass is 17% low because of it. The
mechanism looks structural: `CNEvergreenPhenology` sets `bgtr = 0` and has no
onset event, so an evergreen that loses its canopy has no way to rebuild it,
while the deciduous subroutines re-flush from storage every spring.

- [STATUS_FOR_REVIEW.md](STATUS_FOR_REVIEW.md) - start here. The findings, the
  open questions, the two attributions that turned out to be wrong, and the
  experiment in flight (job 522372).
- [PINE_DIEBACK_HDM_FIRE.md](PINE_DIEBACK_HDM_FIRE.md) - fuller working detail,
  the fire and HDM evidence, the configuration checks, and the cost figures.

Only biomass ever accumulates the imprint. Over the zoom box, GPP, NPP and
0–30 cm SOC hold a block index between 0.90 and 1.02 in every year from 1850 to
2023, while biomass climbs from 0.93 in 1850 to about 1.13 by 2023 as harvest
history builds up. That is expected: biomass is the pool that integrates
decades of wood-harvest disturbance, and the other three are not.
