# High-resolution ELM forest carbon manuscript

Updated: 2026-09-22.

Working title: **High-resolution land modeling reveals spatial opportunities
for forest carbon management in the southeastern United States**.

This directory assembles the manuscript argument and analysis assets across
0.5° and 4 km. The approved contribution is high-resolution ELM, supported by
observational evaluation, spatial heterogeneity/processes, and consequences
for management prioritization.

## Reading order

| File | Role |
|---|---|
| [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) | Authoritative agreed structure, research questions, Methods and writing plan |
| [FIGURE_PLAN.md](FIGURE_PLAN.md) | Five planned main figures; mapping from legacy script numbers |
| [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) | Current interpretation, numerical provenance and evidence status |
| [AI_HANDOFF.md](AI_HANDOFF.md) | Execution context, paths, traps and next work |
| [DF_GRASS_SENSITIVITY.md](DF_GRASS_SENSITIVITY.md) | Current phenology evidence plus dated historical investigation |
| [NBP_RESIDUAL_REVIEW_20260915.md](NBP_RESIDUAL_REVIEW_20260915.md) | Dated source-code/accounting review; not the current paper outline |
| [REVIEW_CODEX_20260915.md](REVIEW_CODEX_20260915.md) | Historical scientific review and correction rationale |
| [outputs/README.md](outputs/README.md) | Status of existing generated assets |

Results have four sections: spatial evaluation; regional futures and benefits;
spatial heterogeneity and mechanisms; spatial prioritization. The priority new
test compares equal-area selections (initial examples 20% and 30%) at both
resolutions. It is planned, not implemented or validated by this update.

## Important version boundary

Existing fig01–fig06 filenames remain stable legacy asset IDs. Their numbers
are not the new manuscript figure numbers. Existing figures and headline
values use older case mappings; new 4 km runs and paired 0.5° phenology tests
are documented outside this directory and have not been merged automatically.

Read [the rerun comparison](../20260908_seus_4km/rerun_comparison/FINDINGS.md)
and [daylength diagnostics](../CRIT_DAYL_STRESS_ARTIFACT.md) before choosing
the manuscript cohort. Configuration differences and parameter-induced
spatial discontinuities matter to any claimed resolution advantage.

## Scope of the September 22 update

- Aligned active planning documents, script descriptions, plot labels and
  diagnostic interpretation text with the agreed story and known evidence.
- Preserved old numerical records in a clearly marked archive and dated
  reviews; retained generated PNGs as legacy outputs.
- Kept numerical algorithms, case dictionaries, data paths, caches and Slurm
  resources unchanged. New selection/evaluation analyses still need execution.

No Pathfinder files were transferred, no jobs were submitted, and no plots
were regenerated in this update. Follow the project and workspace AGENTS.md
for remote operations. Use explicit scoped Git paths; this repository also
contains unrelated work streams.
