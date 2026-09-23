# High-resolution ELM forest carbon manuscript

Updated: 2026-09-23.

Working title: **High-resolution land modeling reveals spatial opportunities
for forest carbon management in the southeastern United States**.

This directory assembles the manuscript argument and analysis assets across
0.5° and 4 km. The approved contribution is high-resolution ELM, supported by
observational evaluation, spatial heterogeneity/processes, and consequences
for management prioritization.

## Reading order

| File | Role |
|---|---|
| [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) | Authoritative agreed structure, research questions, Methods and writing plan; its "Decisions — 2026-09-23" section governs |
| [CASE_MATRIX.md](CASE_MATRIX.md) | The paper's cohort: actual case names, SSPs, scenarios, completion and configuration per resolution |
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

## Decisions of 2026-09-23 (details in the blueprint)

1. **Cohort = the 20260910 rerun family** ([CASE_MATRIX.md](CASE_MATRIX.md)).
   `common.py` still points to the legacy cohort and must be switched before
   any figure is regenerated. All legacy headline numbers are void for the
   paper.
2. **crit_dayl_stress:** analyze the current outputs as if they were the
   38000 s configuration; a full 38000 s rerun may follow. Keep every script
   cohort-swappable (case names only from one mapping).
3. **Fire-map blobs come from the HDM population-density input**; the fire
   component of vulnerability has HDM's coarse effective resolution.

Resolution claims are tested against a downscaled 0.5° field (0.5° per-PFT
density × 4 km PFT fractions) and, for selection, against 4 km aggregated to
0.5°.

## Legacy assets

Existing fig01–fig06 filenames remain stable legacy asset IDs. Their numbers
are not the new manuscript figure numbers, and their values come from the
legacy cohort.

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
