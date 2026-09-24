# High-resolution ELM forest-carbon manuscript

Updated: 2026-09-24.

Working title: **High-resolution land modeling reveals spatial opportunities
for forest carbon management in the southeastern United States**.

High-resolution ELM is the central contribution; forest-carbon management is
the application. The evidence chain is observational evaluation → regional
carbon benefits → spatial heterogeneity and mechanisms → consequences for
equal-area prioritization. The planned five main figures and four Results
sections are described in
[manuscript_figure_results_discussion.md](manuscript_figure_results_discussion.md).

## Directory map

| Location | Purpose |
|---|---|
| [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) | Decisions, Introduction, Methods, tables, closure checklist |
| [manuscript_figure_results_discussion.md](manuscript_figure_results_discussion.md) | The only maintained figure, Results, and Discussion plan |
| [CASE_MATRIX.md](CASE_MATRIX.md) | Case and configuration provenance for the chosen cohort |
| [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) | Evidence status; old numbers are explicitly void for the paper |
| [code/](code/README.md) | Analysis scripts, shared helper, and Slurm runner |
| [figures/](figures/README.md) | Figure output; [legacy/](figures/legacy/) contains older exploratory PNGs only |
| [supplement/](supplement/) | Supporting diagnostics, historical reviews, and supplement planning |

## Current status and boundaries

The intended manuscript cohort is the 20260910 rerun family at 4 km and 0.5°.
The active case map is in [code/common.py](code/common.py); all numerical
claims from the old figure cohort must be recalculated before manuscript use.
The old filenames fig01–fig06 identify exploratory scripts, **not** the five
planned manuscript figures. Current PNGs in [figures/legacy/](figures/legacy/)
were not regenerated from the active cohort.

The paper cohort still uses the original `crit_dayl_stress = 36000 s`; its
outputs are analysed **as if** they were the 38000 s configuration, because
the parameter does not change the analysis design. A full 38000 s rerun may
follow, and the 30.833°N discontinuity is disclosed as a limitation. Only
Default and DF have been rerun at 38000 s so far. Fire-based vulnerability is partly limited by the
coarse-effective-resolution HDM input. Native 4 km versus native 0.5° compares
two configurations, not grid spacing alone; aggregation of one 4 km simulation
provides the cleaner spatial-information comparison.

Run code on Pathfinder through approved Slurm jobs, not on the login node.
From this directory the runner and script paths are now, for example,
`code/submit_py.sbatch code/fig01_offset_potential_timeseries.py 4km`.
This is a path example, **not** permission to sync or submit a job. The project
root is scratch-backed and remote files may be purged; see the project and
workspace AGENTS.md before any remote action. No remote files or jobs were
changed by this local reorganization.
