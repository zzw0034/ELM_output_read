# AI handoff — high-resolution ELM forest carbon manuscript

Updated: 2026-09-22. Read [README.md](README.md), then
[MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md). The blueprint records the
user-approved argument; [FIGURE_PLAN.md](FIGURE_PLAN.md) maps existing scripts
to the new manuscript figures. [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)
separates legacy numerical results from newer evidence and planned tests.

## Agreed scientific direction

High-resolution ELM is the central contribution, with forest carbon management
as the application. Results follow four questions:

1. Which observed spatial patterns does 4 km capture relative to 0.5°?
2. How consistent are regional futures and management benefits?
3. What local heterogeneity and carbon processes do regional totals conceal?
4. How does resolution change equal-area spatial prioritization?

The priority new test selects the same physical area (initially 20% and 30%)
at each resolution and compares location overlap, captured modeled carbon,
and vulnerability. It is not implemented by the existing quadrant script.
Do not promise a positive result or treat 4 km as observational truth.

## Run provenance — resolve before regenerating manuscript figures

The current `common.py` dictionaries are the **legacy figure cohort**:
0.5° 20260911 dt3600 cases plus older 4 km 20260908 futures, with management
comparisons restricted to SSP3-7.0. Existing 4.79/4.95 PgC and 3–5% resolution
differences belong to that cohort; they are not refreshed rerun estimates.

Newer analyses document additional management SSPs and changed 4 km outputs:
[rerun comparison README](../20260908_seus_4km/rerun_comparison/README.md) and
[FINDINGS](../20260908_seus_4km/rerun_comparison/FINDINGS.md). Do not say the
whole project still has only seven futures per resolution. Build an actual
case/version matrix before expanding or replacing the manuscript cohort.

The same comparisons record differences in restart, parameter files and
other configuration changes. Current cross-resolution agreement alone cannot
isolate a pure grid-spacing effect.

## Grass phenology — newer evidence supersedes the September 15 hypothesis

[CRIT_DAYL_STRESS_ARTIFACT.md](../CRIT_DAYL_STRESS_ARTIFACT.md) documents a
36000 s daylength threshold producing a spatial discontinuity near 30.833°N
in both resolutions, and September 22 paired Default/DF sensitivity runs at
38000 s for four 0.5° SSPs. See [DF_GRASS_SENSITIVITY.md](DF_GRASS_SENSITIVITY.md).

The paired sensitivity changes cumulative NBP avoided-loss benefits by about
+5.3–5.9%; this is a different outcome from the legacy decade-mean
TOTECOSYSC benefits. The starting restart still uses the original parameter.
The test does not establish that 38000 s is ecologically optimal.

This matters directly to the new paper: a finer map can expose a parameter
artifact as well as useful spatial structure. Quantify its influence on
heterogeneity, observed skill, and selections before calling extra detail an
advantage. Do not silently substitute sensitivity cases for baseline cases.

## Paths and execution

- Project remote root: declared in ../../AGENTS.md as
  `/scratch/hpcl-cli185/zw5/ELM_output_read`.
- Analysis working directory there: `analyses/paper_carbon_offset`.
- `common.py` still references legacy raw files under
  `/scratch/hpcl-cli185/zw5/cime_output_dirs`; availability is unverified.
- Poster scripts record an archive location for older 4 km output:
  `/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260901_before_seus_rerun`.
  Treat this as a documented location to verify, not proof files exist today.
- Scenario definitions:
  `../../../ELM_Futu_landuseInput/harvest_scenarios/HARVEST_SCENARIOS.md`.

Follow workspace/project AGENTS.md. Before any remote inspection, read the
project declaration and local git status. Before transfers state direction;
commit scoped changes first. Remote writes/submissions need the required
user approval. Use scp for approved small files or rsync without --delete.
Remote Python analysis belongs on Slurm, including 0.5°. Existing runner:

```bash
sbatch --export=NONE -J <name> submit_py.sbatch <script.py> [args...]
```

This is a command template, not authorization to submit. Verify input paths,
environment, log directory and resources; use sbatch --test-only before a
production submission. The current runner requests 1 node, 1 task, 1 CPU,
32 GB and 3 hours on hpcl-cli185; adjust from workload evidence. For dependent
analysis require successful extraction (afterok), or explicitly validate
complete inputs if using another dependency policy.

## Accounting and implementation traps

- RF = restoration/protection with broad zero harvest; RH = prescribed
  harvest-rate reduction; DF = idealized forest-to-grass avoided-loss bound.
- Preserve the signs RF−Default, RH−Default, Default−DF.
- TOTECOSYSC differences are ecosystem stock benefits, not cumulative NBP,
  marketable credits, or independently evaluated climate benefits.
- Pool sums do not yet close against TOTECOSYSC. The provisional 66–70%
  aboveground increment share is not the 18–19% standing-stock share.
- Exact NBP budget: NEP − COL_FIRE_CLOSS − LAND_USE_FLUX.
  PFT_FIRE_CLOSS omits decomposition-pool fire loss. Inferring full fire
  closes the identity by construction; it does not validate fire physics.
  The older “unidentified NBP residual” explanation is superseded by
  NBP_RESIDUAL_REVIEW_20260915.md; the stock-pool residual is still separate.
- FIRE is emitted infrared radiation. FAREA_BURNED is annualized as a rate in
  the existing scripts; retain source/version checks for its misleading units.
- Fire loss is already reflected in the simulated stock benefit. Fire/stock
  is loss intensity, not reversal probability. fig05/fig06 currently use PFT
  fire loss, not complete column loss.
- fig05 actually uses annual mean BTRAN, not growing-season BTRAN; its
  component ranks are cell-count based, while quadrant medians are
  area-weighted. Its decadal stock CV is not detrended. These definitions
  require review before publication and before cross-resolution selection.
- Mask ocean/inactive cells, use physical area weights and calendar-aware
  monthly aggregation. Audit missing-data handling, year/grid alignment and
  cache provenance. Existing caches lack complete version signatures.

## Next work in order

1. Freeze case/run/parameter provenance and decide the matched manuscript
   cohort using the existing new-run evidence.
2. Quantify AGB/SOC spatial skill using the poster's available inputs; the
   visual comparison exists, but the formal benchmark is pending.
3. Implement within-cell heterogeneity and equal-area selection diagnostics,
   checking sensitivity to the daylength artifact and reference fields.
4. Close pool accounting and harmonize fire/vulnerability definitions;
   retain DF sensitivity and RF management-area constraints.
5. Rebuild and visually review the five planned main figures.

The September 22 directory update changes documentation, captions and
interpretation messages. It does not recompute outputs, change case mappings,
implement the planned selection test, or submit simulations.
