# High-resolution ELM forest-carbon manuscript

Updated: 2026-09-24.

Working title: **High-resolution land modeling reveals spatial opportunities
for forest carbon management in the southeastern United States**.

High-resolution ELM is the central contribution; forest-carbon management is
the application. The evidence chain is observational evaluation → regional
carbon benefits → spatial heterogeneity and mechanisms → consequences for
equal-area prioritization. The planned five main figures and four Results
sections are described in
[MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) Part E.

## Directory map

| Location | Purpose |
|---|---|
| [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) | The single manuscript plan: decisions, story, Introduction, Methods, figures/Results, Discussion, tables, checklist |
| [ANALYSIS_FRAMEWORK.md](ANALYSIS_FRAMEWORK.md) | Short English outline of the analysis framework for sharing; derived from the blueprint, which governs |
| [CASE_MATRIX.md](CASE_MATRIX.md) | Earlier case/configuration audit; Default/DF mapping still needs the 2026-09-24 update |
| [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) | Evidence status; old numbers are explicitly void for the paper |
| [analysis_process_notes.md](analysis_process_notes.md) | Data locations, sources, scripts, processing conventions and provenance checks |
| [code/](code/README.md) | Analysis scripts, shared helper, and Slurm runner |
| [figures/](figures/README.md) | Figure output; [legacy/](figures/legacy/) contains older exploratory PNGs only |
| [supplement/](supplement/) | Supporting diagnostics, historical reviews, and supplement planning |

## Current status and boundaries

The intended manuscript cohort is the 20260910 rerun family at 4 km and 0.5°.
The 46 chosen directories are recorded in [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) §0.
Every management difference is parameter-matched: RF/RH against the 36000 s
Default, DF against the `cds38000` Default (blueprint Part A2).
[code/common.py](code/common.py) still has only the 36000 s mapping and must
gain the `cds38000` Default/DF pair before rerunning analyses.
All numerical claims from the old figure cohort must be recalculated before manuscript use.
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
