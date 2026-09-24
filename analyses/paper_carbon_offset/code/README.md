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
