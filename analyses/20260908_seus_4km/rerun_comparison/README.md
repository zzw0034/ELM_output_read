# 20260910 rerun vs 20260908 SEUS 4 km comparison

This subfolder compares the matched members of the newest 4 km family under
`/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun` with the older
family archived under
`/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260901_before_seus_rerun`.

## Paired scope

- Transient, 1850-2023
- SSP1-1.9, SSP2-4.5, SSP3-7.0, and SSP5-8.5, 2024-2100
- SSP3-7.0 RF, DF, and RH, 2024-2100

The rerun also contains RF/DF/RH members for SSP1-1.9, SSP2-4.5, and
SSP5-8.5.  The 20260908 family has no matching cases, so they are intentionally
excluded from old-minus-new plots.

## Variables and units

- `GPP`, `NPP`, `NBP`, and `PFT_FIRE_CLOSS`: monthly mean rates in
  gC m-2 s-1. Each record is multiplied by its exact `time_bounds` duration
  in seconds and summed to an annual total.
- `FAREA_BURNED`: treated as a rate in s-1 even though the history attribute
  says `units='proportion'`. Monthly burned fraction is
  `monthly_mean_rate * days_in_record * 24 * 3600`; annual fraction is the
  sum of the monthly fractions. Domain physical burned area uses
  `fraction * area[km2] * landfrac`, and is reported in km2 yr-1.
- Soil C 0-30 cm: `SOIL1C_vr + ... + SOIL4C_vr` (gC m-3), integrated through
  0.30 m with partial weighting of the layer crossed by the cutoff.
- Soil C 0-100 cm: native `TOTSOMC_1m` (gC m-2).

All domain means use `area * landfrac`; ELM's history variables are not
already land-fraction weighted.

## Products

- Seven time-series figures, one per requested variable, with all eight
  matched cases shown in panels.
- Spatial old/new/difference figures for the recent historical decade and
  the early/end-of-century windows of each future case.
- `summary.csv` with paired early and recent/end-period means, absolute
  changes, and percent changes.
- `annual_series.csv` with old, new, and new-minus-old values for every year.
- `RESULTS.md` with a compact human-readable summary.
- `FINDINGS.md` with interpretation of temporal and spatial differences.
- Seven `delta_timeseries_*.png` figures showing new minus old by year.

The raw 4 km files must only be processed through Slurm.  Run the extraction
array first, then submit `submit_plot.sbatch` with an `afterok` dependency on
the array job.

Once the 16 compact `_cache/*.nc` files have been copied to this folder on
the local Mac, `Rscript plot_cached_deltas_local.R` can also make the annual
CSV and delta time-series figures locally, using the installed `ncdf4` and
`ggplot2` packages. This does not read the raw 4 km files.
