# Analysis code

These are exploratory scripts and diagnostics, not yet the final five
manuscript figures. The numbered filenames are stable legacy asset IDs.
See [the current figure plan](../manuscript_figure_results_discussion.md) and
[case matrix](../CASE_MATRIX.md) before interpreting output.

| Existing script | Intended use in the new paper | Required work |
|---|---|---|
| `fig01_offset_potential_timeseries.py` | Main Figure 2 | Recompute regional RF/RH/DF benefits across SSPs |
| `fig02_offset_potential_maps.py` | Main Figure 3 or supplement | Harmonize mask and area-weighted spatial summaries |
| `fig03_carbon_pool_partitioning.py` | Main Figure 4 | Close pool sums against native TOTECOSYSC |
| `fig04_resolution_comparison.py` | Main Figures 2–3 | Extend aggregation comparison from DF to RF |
| `fig05_siting_potential_vs_vulnerability.py` | Starting point for Main Figure 5 | Replace quadrants with equal-area selection; audit risk definitions |
| `fig06_fire_impact.py` | Supplement / vulnerability support | Use complete fire budget and account for HDM effective resolution |
| `check_nbp_decline_decomposition.py` | Mechanism/accounting support | Validate the NBP components for the selected cohort |
| `check_df_grass_decomposition.py`, `check_grass_phenology_mechanism.py` | Supplementary diagnostics | Interpret alongside corrected daylength runs |

Observation data fetchers (Figure 1 inputs):

| Script | Output | How it was run |
|---|---|---|
| `obs_fetch_esacci_agb_v7_seus.py` | ESA CCI Biomass v7.0 1 km AGB/AGB_SD, all 18 epochs, SEUS box 24–37.5°N, 95–74°W, in `/projects/hpcl-cli185/proj-shared/zw5/obs_data/biomass/` | 2026-09-24 on the Pathfinder login node (network transfer only, HTTP byte-range read from CEDA), streamed over ssh stdin with the `make_surfdata_pf` python; values unchanged (oven-dry biomass, Mg/ha, ocean = 0) |

The missing main analyses are quantitative AGB/SOC observational evaluation,
within-0.5°-cell skill, and equal-area selection. Their absence should not be
obscured by the old figure filenames.

`common.py` is the single case map and common loader. New figures write to
`../figures/<PAPER_COHORT>/` on Pathfinder, and cache files remain in
`../_cache/<PAPER_COHORT>/`. The generated legacy PNGs are preserved in
`../figures/legacy/`.

From the **analysis root** (the parent of this directory), the approved-run
command shape is:

```bash
sbatch --export=NONE -J <name> code/submit_py.sbatch code/<script.py> [args...]
```

This is not authorization for remote synchronization or submission. Follow
the project AGENTS.md, verify remote files and resources, and submit only
after the required approval.
