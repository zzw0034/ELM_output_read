# Figure plan — high-resolution ELM forest carbon manuscript

Updated: 2026-09-23. The approved story is in
[MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md); its 2026-09-23 decisions
(new-rerun cohort, current outputs treated as 38000 s, HDM fire structure)
govern. All figures are rebuilt from [CASE_MATRIX.md](CASE_MATRIX.md). High-resolution ELM is
central throughout: observational skill → spatial heterogeneity/processes →
consequences for prioritization. CMIP6/TRENDY provides concise regional context.

## Four Results sections and five planned main figures

| Main figure | Results | Scientific purpose | Existing material | Required development |
|---|---|---|---|---|
| 1. Spatial credibility | 3.1 Spatial representation and observational evaluation | Test which observed patterns 4 km captures relative to 0.5° | Poster AGB/SOC comparisons, including three-column variants | Harmonize masks, units, years and depth; quantify common-support and within-coarse-cell skill |
| 2. Regional futures and benefits | 3.2 Regional carbon futures and management benefits | Establish baseline trajectories, effect sizes and cross-resolution consistency | Legacy fig01; scenario-family NBP plots; fig04 totals | Freeze matched case versions; reconcile headline numbers; show early/mid/late horizons |
| 3. Heterogeneity hidden by aggregation | 3.3 Spatial heterogeneity and carbon mechanisms | Separate aggregation loss from configuration differences | Legacy fig02 maps and fig04 native/aggregated comparison | Within-cell variation, RF-focused tails, reproducible subregions and daylength-artifact checks |
| 4. Carbon mechanisms | 3.3 | Explain management benefits and local patterns | Legacy fig03; NBP decomposition diagnostic | Close pool residual, add spatial strata, keep stock and flux boundaries distinct |
| 5. Consequences for prioritization | 3.4 Consequences for spatial prioritization | Measure what equal-area selections change | Legacy fig05 quadrants and poster panel 4 | New 20%/30% selection comparison, area-budget curves, overlap, benefit and vulnerability metrics |

Five figures are a working target. Split crowded panels if necessary while
preserving the four-part argument. Fire diagnostics support mechanisms and
vulnerability; they are not the title-level story.

## Existing filenames are legacy asset IDs

Do not rename existing scripts or PNGs simply to match manuscript numbering.
They have dependencies and cached results. Use this mapping:

| Existing script | New role | Current scope / limitation |
|---|---|---|
| fig01_offset_potential_timeseries.py | Main 2 | SSP3-7.0 stock benefits; legacy case cohort |
| fig02_offset_potential_maps.py | Main 3 / supplement | Three management maps; not observed spatial skill |
| fig03_carbon_pool_partitioning.py | Main 4 | Selected-pool sums, unclosed against native TOTECOSYSC |
| fig04_resolution_comparison.py | Main 2 totals + Main 3 heterogeneity | Spatial panels use DF; extend to RF for the central management example |
| fig05_siting_potential_vs_vulnerability.py | Starting material for Main 5 | Median quadrants, not an equal-area selection experiment |
| fig06_fire_impact.py | Supplement + supporting vulnerability | PFT fire loss, not complete column fire; not reversal probability |
| check_nbp_decline_decomposition.py | Main 4 / supplement | Full-column fire inferred from exact NBP identity |
| check_df_grass_decomposition.py | Supplement / accounting check | Partial pools, no independent sensitivity conclusion |
| check_grass_phenology_mechanism.py | Historical screening diagnostic | Default domain means; newer paired sensitivity evidence is elsewhere |

Poster sources are in ../carbon_offset_poster/codes/ and outputs/.
plot_biomass_soc_panel.py already has 0.5° | 4 km | observation variants.
Its docstring explicitly calls the comparison illustrative. New quantitative
evaluation and equal-area selection scripts do not yet exist in this folder.

## Figure 1: evidence for spatial credibility

Match ELM/ESA-CCI biomass-carbon definitions, masks and 2014–2020 coverage.
Compare SOC at 0–30 cm; SoilGrids is not a contemporaneous annual time series.
Report bias, RMSE, spatial correlation and distribution agreement on common
support. Independently test whether 4 km anomalies within 0.5° cells correspond
to observed anomalies. Do not equate sharper spatial texture with accuracy.
Show four columns — native 0.5° | downscaled 0.5° | native 4 km |
observation — so skill from 4 km land cover (A→B) is separated from skill from
running at 4 km (B→C).

The 30.833°N daylength discontinuity must be identified in relevant fields.
Its increased visibility at 4 km is not evidence of improved realism.

## Figures 2–4: quantitative definitions and provenance

Use RF−Default and RH−Default as additional ecosystem storage, Default−DF as
an idealized avoided-loss bound. RF includes restoration and broad protection/
zero harvest. Report TOTECOSYSC differences separately from cumulative NBP.

Legacy 2091–2100 benefits (RF 4.95/4.79, RH 0.98/0.93, DF 9.88/9.50 PgC)
and poster RF 5.9/DF 10.1 are void for the paper; recompute on the new cohort.

Use three spatial representations: native 4 km, 4 km area-weighted to 0.5°,
and native 0.5°. Distinguish averaging effects from differences in parameter
files, restarts, inputs and other configuration. Quantify distributions with
land-area weighting; some existing percentile/RMS diagnostics are unweighted.

The provisional 66–70% aboveground increment share requires pool closure.
The large standing SOC pool does not imply large additional SOC storage.
Use signed contributions, keeping litter/CWD distinct from belowground pools.

## Figure 5: priority new analysis

Follow Methods 2.9 of the blueprint:

- Coarse comparators: 4 km aggregated to 0.5° (primary; same simulation),
  downscaled 0.5°, native 0.5°. Compare selection overlap across SSPs with
  overlap across resolutions where management runs exist for several SSPs.
- Report the fire component separately and repeat selections without it; its
  spatial structure comes from the coarse HDM input.
- Choose a common eligible domain and identical area budgets, initially 20%
  and 30%, then a selection curve. Regional land is not automatically land
  available for restoration, especially for the RF policy bundle.
- Apply the same potential definition and period; compare potential-only
  selection with explicit vulnerability screens. Define cutoff/tie handling.
- Map both selections to common support without using fine-scale information
  to choose preferred pixels inside a coarse selected cell.
- Measure area overlap, captured PgC, share of total potential, benefit per
  selected hectare, and separate vulnerability components.
- Score both masks against the same reference fields; disclose the advantage
  inherent in ranking and evaluating against the same 4 km field. Include
  alternative-reference/common-coarse-support checks and observational skill.
- Test weights, thresholds, time windows, eligibility and phenology sensitivity.
  Do not assume that 4 km must outperform.

The legacy 4 km RF quadrant (33.6% of land, 57.3% of potential) is void for
the paper. A quadrant is the high-potential AND low-vulnerability
intersection, not the whole low-vulnerability half.

Existing vulnerability is an equal-weight mean of cell-rank-normalized
PFT_FIRE_CLOSS/TOTECOSYSC, annual 1−BTRAN, and non-detrended decadal stock CV.
Quadrant cutoffs use area-weighted medians. Review the definitions and missing
components before treating this as a robust cross-resolution selection metric.

## Supplement and output status

Keep full historical/scenario trajectories, CMIP6/TRENDY context, detailed
fire budgets/maps, pool closure, DF phenology sensitivity, input/configuration
audits and selection robustness in the supplement.

Existing outputs/ PNGs are legacy exploratory assets. They were not regenerated
by the September 22 documentation update and may retain superseded labels.
See outputs/README.md before reuse. A final figure release must record case
names, parameter version, source commit, variable definitions, windows and
cache provenance, and undergo visual review.
