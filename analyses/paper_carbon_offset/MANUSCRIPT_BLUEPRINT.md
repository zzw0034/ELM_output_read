# Manuscript blueprint: high-resolution ELM and southeastern U.S. forest carbon management

Last updated: 2026-09-29

This is the **single maintained plan** for the manuscript: decisions, story,
Introduction, Methods, figures/Results, Discussion, tables and the closure
checklist. It merges the former `manuscript_figure_results_discussion.md`
(2026-09-28; the old text is in Git history). It reports no newly calculated
results; every number must be recomputed from the paper cohort.

Two rules keep this file consistent:

- **Each analysis procedure is written once, in Part D (Methods).** Part E
  (figures/Results) states the question, the panels and the interpretation,
  and points to the Methods subsection.
- **Part A holds the only statement of current decisions.** Superseded
  decisions are deleted here, not annotated; Git history keeps them.

Data locations, sources and processing conventions:
[analysis_process_notes.md](analysis_process_notes.md). Evidence status:
[RESULTS_SUMMARY.md](RESULTS_SUMMARY.md).

---

## Part A — Current decisions

### A1. Direction (agreed 2026-09-22)

High-resolution ELM is the central contribution; forest-carbon management is
the application. Resolution is a thread through every Results section, not a
final sensitivity subsection. Fire is a mechanism and a vulnerability
component, not the title-level story.

### A2. Cohort and parameter pairing (decided 2026-09-29)

All outputs come from
`/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/`. The full
4 SSP × Default/RF/RH/DF design exists at both resolutions. Every management
difference is taken between runs with the **same** `crit_dayl_stress`:

| Comparison | Management run | Default run it is paired with | Parameter |
|---|---|---|---|
| RF − Default, RH − Default | RF/RH (no suffix) | Default without suffix (0.5° `20260911_…_future_<ssp>_dt3600`; 4 km `20260917_seus_4km_fut_<ssp>`) | 36000 s |
| Default − DF | DF `cds38000` | Default `cds38000` | 38000 s |

So each SSP and resolution has two Default runs, one per pairing. Spin-up and
transient runs use 36000 s. This makes 46 directories (40 futures, 6
spin-up/transient); the list is in [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) §0.

Consequences:

- The Default trajectories in Figure 2 use the 36000 s Default: it continues
  the 36000 s transient without a parameter change in 2024 and is the
  baseline for RF and RH. The 38000 s Default appears only inside the DF pair.
- The 30.833°N discontinuity remains in the RF/RH pair and is disclosed; the
  DF pair, where it was strongest, is free of it.
- Figure 5 (RF − Default) and the vulnerability components (from the RF run)
  are therefore all at 36000 s.

`code/common.py` and [CASE_MATRIX.md](CASE_MATRIX.md) must be updated to this
pairing before any analysis.

Legacy headline values (RF 4.79/4.95, RH 0.93/0.98, DF 9.50/9.88 PgC; the
3–5% resolution difference; the 33.6%/57.3% quadrant; poster RF 5.9 and
DF 10.1 PgC) are void for the paper.

### A3. HDM and fire

The circular structures in 4 km fire fields come from the HDM
(population-density) input, bilinearly interpolated from 0.5°. The same SSP2
HDM is used for every SSP, and lightning is a fixed 1995–2011 climatology.
4 km fire therefore has roughly 0.5° effective resolution and no
scenario-specific ignition signal. Report fire separately and test every
selection with and without it (D7, D9).

### A4. Coarse comparators for the resolution argument

| Field | What it knows |
|---|---|
| A. native 0.5° run | coarse-cell mean only, from a separately configured run |
| B. downscaled 0.5° | 0.5° per-PFT carbon density × 4 km PFT fractions: 4 km land cover, 0.5° climate/soil/process |
| C. native 4 km run | 4 km land cover plus 4 km climate, soil and their nonlinear process response |
| C′. 4 km aggregated to 0.5° | the 4 km run area-averaged: same simulation, coarse information |

A→B is the value of fine land-cover input; B→C is the value of running the
model at 4 km. Only B→C supports "high-resolution *modeling*". For
prioritization the primary coarse comparator is C′ (no configuration
confound); B and A are secondary. SOC has no B (D6).

### A5. SOC evaluation depths and products (decided 2026-10-01)

Figure 1 SOC is shown at **0–30 cm and 0–100 cm**, against **SoilGrids 2.0 and
HWSD v1.2** (one figure per product), on the ELM 4 km grid. ELM 0–30 cm is the
overlap integral of SOIL1–4C_vr; ELM 0–100 cm is `TOTSOMC_1m` (identical to the
same integral of SOIL1–4C_vr to 1 m, checked). Litter and CWD are excluded.
HWSD v1.2 is coarser (0.05°) than 4 km and is remapped, so it adds no
within-cell information; SoilGrids is requested from the ISRIC WCS directly on
the ELM grid (server-side resampling). D6 step 1 still reads "0–30 cm,
SoilGrids" and has **not** been updated to this wider scope; which product and
depth carry the within-cell test is open. Details and first statistics: [analysis_process_notes.md](analysis_process_notes.md) §3.4.

### A6. Figure 5 choices (decided 2026-10-01/02)

Coarse comparator = the native 0.5° run (not the 4 km map averaged to 0.5°), as in Figure 3. Risk = fire loss and water stress only
(water stress = 1 − BTRAN averaged April–October; NBP variability dropped because about half of it is fire). One threshold per
component, the area-weighted 80th percentile of the 4 km component over eligible land, shared by both resolutions (50th, 90th and
95th as sensitivity). Eligible land = RF 2060 forest fraction ≥ 5 % (results unchanged for floors of 1–20 %). **Main figure**: a RF
benefit without fire loss (stock difference plus the cumulative fire-loss difference since 2024; an approximation), b fire risk,
c water stress, d 4 km siting after removing land above either threshold. The 4 km vs 0.5° comparison (agreement map, budget curve,
exposure), the risk maps and the screen comparison go to the supplement. **Other SSPs (2026-10-02)**: every SSP uses the fixed
SSP3-7.0 p80 thresholds (absolute, not each SSP's own percentile) and one shared colour scale per map panel; main text keeps SSP3-7.0, and the
cross-SSP change of the siting is shown by one map only (how many of the four SSPs select each 4 km cell, four distinct hues;
user decisions 2026-10-02), as Figure 5e or a supplement figure (layout open). Details: [analysis_process_notes.md](analysis_process_notes.md) §3.18–3.20, §3.22.
**Median variant (2026-10-06, under review):** Figure 5 redrawn with the poster method, 4 km only: benefit = net carbon benefit (RF − Default
TOTECOSYSC, fire loss not added back; user decision 2026-10-06) split at its median (not a 20 % budget), risk = composite vulnerability (mean area-weighted percentile rank of fire and water stress) split at its median, each SSP its own area-weighted
medians over eligible land; panels (2 × 2 since 2026-10-06) a benefit, b composite vulnerability, c quadrants, d scatter; the fire and water maps are not in it. SSP3-7.0 drawn first (high benefit / low
risk 34.9 % of eligible land, 57 % of the benefit); other SSPs once the figure is final. This reintroduces the composite and the median split
that E5 had dropped; whether it replaces the 20 %/p80 main figure is open. Details: notes §3.23.

---

## Part B — Scientific story

### B1. Central question

What information does high-resolution land modeling reveal about
southeastern U.S. forest carbon management that regional totals conceal, and
does that information change modeled benefits and priority locations under
future global change?

### B2. One-sentence answer (to be confirmed by the tests)

High-resolution ELM can translate similar regional carbon-benefit totals into
spatially differentiated management opportunities by resolving local
heterogeneity in carbon gains and modeled vulnerability; observational skill
and equal-area selection tests determine how far that claim holds.

### B3. The four-step framework

| Step | Results | Figure | Question it answers | Coarse comparison used |
|---|---|---|---|---|
| 1. Test spatial patterns against observation-based estimates | 3.1 | 1 | Is the extra spatial detail of 4 km ELM credible, and is it more than fine land cover alone explains? | native 0.5°; downscaled 0.5° (AGB) |
| 2. Establish regional carbon trajectories and modeled management benefits | 3.2 | 2 | How much carbon does management add, and do the two resolutions agree on the regional totals? | native 0.5° |
| 3. Quantify spatial heterogeneity and explain its carbon-pool and process contributions | 3.3 | 3, 4 | What local differences do the regional totals hide, and where do they come from? | 4 km aggregated to 0.5°; downscaled 0.5° |
| 4. Test whether that information changes equal-area management priorities | 3.4 | 5 | Does the spatial information change where to manage, for the same area budget? | 4 km aggregated to 0.5° (primary); downscaled; native 0.5° |

The steps build on each other:

1. **Credibility first.** Without evidence that the 4 km detail is credible,
   no later conclusion based on 4 km spatial patterns has a basis.
2. **Then the regional totals.** They set the size of the benefits. If the two
   resolutions give similar totals, the next question follows naturally: what
   do those similar totals hide?
3. **Then open the totals.** Quantify the spatial information removed by
   aggregation, and explain it with carbon pools and processes.
4. **Finally the decision.** Test whether that information changes which land
   would be chosen for the same area budget. This is the applied conclusion.

Resolution is the thread through all four steps: every step compares 4 km
with a coarse alternative (last column), so it is not a sensitivity section
added at the end.

### B4. Language

- RF − Default and RH − Default: **modeled additional carbon storage**; DF:
  Default − DF, a **modeled avoided-loss bound**.
- The stock metric is TOTECOSYSC, which includes product pools (D4); call it
  ecosystem-and-product carbon, or define it on first use.
- RF is a **restoration/protection bundle** (restoration plus zero harvest on
  existing forest); RH reduces prescribed harvest; DF is idealized
  instantaneous forest-to-grass conversion without succession.
- "Carbon-offset potential" only when linking to the proposal or crediting
  context, never as issued credits. The simulations establish no legal
  additionality, leakage, durability or credit quantity.

---

## Part C — Titles and Introduction

### C1. Working titles

> High-resolution land modeling reveals spatial opportunities for forest
> carbon management in the southeastern United States

Alternative: *From regional carbon potential to spatial prioritization:
high-resolution land modeling of southeastern U.S. forest management.* Avoid
"climate-driven fire losses" until the fire increase is attributed.

### C2. Introduction, four paragraphs

1. **Importance.** Southeastern U.S. forests are a large, actively managed
   carbon system where regrowth, harvest, land conversion and disturbance act
   on similar time scales. Keep this paragraph about the carbon cycle, not
   the credibility of voluntary markets.
2. **One organizing gap: spatial scale.** Regional assessments quantify broad
   trajectories but do not show where reforestation or reduced harvest yields
   the largest modeled benefit at acceptable modeled disturbance exposure.
   Similar regional totals can arise from very different local distributions
   of land cover, management change, carbon pools and risk; whether resolving
   that heterogeneity changes equal-area priorities is largely untested.
   Accounting boundaries (which pools, including soil and products, count) and
   disturbance risk to persistence are context, not separate gaps. Do not
   assert that crediting studies generally omit soil carbon. The Default
   scenario is a comparison convention, not the gap.
3. **Existing approaches.** Inventory estimates, remote-sensing/static
   potential maps and process models. State exactly which estimates disagree
   and whether the disagreement concerns current stocks, biophysical potential
   or additional future storage; do not claim sign disagreement without
   matched definitions. Few studies jointly resolve dynamic land use, multiple
   pools, disturbance and spatial scale with management scenarios against a
   defined Default. CMIP6/TRENDY: brief regional context only, since
   inter-model spread does not isolate resolution.
4. **Approach.** ELM at 0.5° and 4 km, four SSPs, Default/RF/RH/DF; state the
   DF and RF definitions before Results; end with the four questions of B3.

---

## Part D — Methods (manuscript §2)

### D1 (2.1). Region and ELM configuration

Domain, land area, PFT representation, carbon pools, fire module, absence of
forest age cohorts. The 4 km grid nests exactly 12 × 12 in the 0.5° grid; land
fraction enters all domain integrals. Document the 4 km surface-data and
land-use workflow and the area-weighted 0.5° aggregation.

Include a table of the **effective resolution of each driver** (Table 1):

| Driver | 4 km run | 0.5° run |
|---|---|---|
| Meteorology | TESSFA2 native | TESSFA2 aggregated |
| Surface data, PFTs, land use/harvest | 4 km | aggregated from 4 km |
| HDM (fire) | bilinear from 0.5°, SSP2 for all SSPs | native 0.5°, SSP2 |
| Lightning | 1995–2011 climatology, T62 | same |
| N deposition, aerosol | 1.9° × 2.5° | same |
| CO2 | global | same |

Only drivers resolved at 4 km can produce genuine 4 km process structure.
Native 0.5° versus 4 km is a comparison of two configurations (separate
spin-ups as well), not of grid spacing alone.

### D2 (2.2). Forcing, spin-up and historical simulation

Meteorological source and downscaling; spin-up protocol for each resolution;
1850–2023 transient; CO2, N deposition, land use and harvest forcing; why
interventions start in 2024 rather than the proposal's 2015.

### D3 (2.3). Future and management experiments

Table 1 lists the actual runs (A2), not the proposal's factorial design. State
the `crit_dayl_stress` value of each run and the pairing rule of A2 (every
difference is parameter-matched). Disclose the 30.833°N discontinuity produced by 36000 s
([CRIT_DAYL_STRESS_ARTIFACT.md](../CRIT_DAYL_STRESS_ARTIFACT.md)). Within a
resolution every future run starts from the same 2024 restart, so paired
differences are zero at the 1 January 2024 state; the 2024 annual means already
include the management effect (DF converts nearly all forest in the first year,
notes §3.6).

### D4 (2.4). Carbon accounting

```text
Restoration/protection benefit(t) = C_RF(t) − C_Default(t)
Reduced-harvest benefit(t)        = C_RH(t) − C_Default(t)
Avoided-loss bound(t)             = C_Default(t) − C_DF(t)
```

`C` is TOTECOSYSC. In this ELM version (`ColumnDataType.F90`, checked
2026-09-24):

```text
TOTECOSYSC = TOTVEGC + CWDC + TOTLITC + TOTSOMC + TOTPRODC
TOTPRODC   = PROD1C + PROD10C + PROD100C
```

TOTPRODC is inactive by default and absent from our h0 files; derive it as
TOTECOSYSC − (TOTVEGC + CWDC + TOTLITC + TOTSOMC), and verify it is near zero
in early transient years. `TOTVEGC_ABG` gives aboveground vegetation carbon.
Close any pool partition with TOTVEGC and the product term; the legacy
several-percent residual most likely came from omitting products and the
vegetation storage/transfer pools.

Report benefits at **three boundaries**: aboveground vegetation, in-situ
ecosystem (excluding products) and ecosystem + products. RF and RH act on the
product pool directly.

```text
NBP = NEP − COL_FIRE_CLOSS − LAND_USE_FLUX
LAND_USE_FLUX = land-conversion loss + product-pool loss
```

WOOD_HARVESTC transfers carbon to products and is not an immediate emission.
Cumulative NBP differs from the stock change when boundaries differ. Fire
losses are already in the modeled net outcome and are never subtracted again.

### D5 (2.5). Aggregation in time and space

Day-weighted monthly means from `time_bounds`; complete-year checks; land
masks; area × landfrac weighting; PgC conversion. Windows: historical
2014–2023, future early/mid/late, and 2091–2100. Event years are described as
events, not as monotonic decline.

### D6 (2.6). Observational evaluation (Figure 1)

1. **Matching.** AGB: ESA CCI Biomass v7.0 1 km, carbon = 0.50 × dry AGB
   (sensitivity 0.47–0.51),
   matched to the model years (source, subset and conversion in
   [analysis_process_notes.md](analysis_process_notes.md) §3.1; the older
   0.04° v5.01 file used by the poster is superseded). SOC: 0–30 cm, SoilGrids,
   a spatial estimate rather than an annual series. Same valid mask and area
   denominator for all fields.
2. **Common support.** Aggregate observations and the 4 km run to 0.5°;
   compare both resolutions with observations by signed bias, RMSE, spatial
   correlation and distribution.
3. **Within coarse cells.** Aggregate observations to the 4 km grid. In each
   0.5° cell, subtract the cell mean of the valid fine cells from the
   observations, and the same cells' mean from the 4 km model. Compare the two
   anomaly fields (correlation, RMSE, amplitude). The native 0.5° field has
   zero anomalies at this scale.
4. **Downscaled comparator (AGB only).** Compare the 4 km anomalies with those
   of field B (A4), built from 0.5° per-PFT vegetation carbon (h1 LEAFC,
   LIVESTEMC, DEADSTEMC) and 4 km PFT fractions.
5. **Why SOC has no downscaled comparator.** All natural PFTs (and crops,
   `create_crop_landunit=.false.`) share one soil column, so coarse SOC cannot
   be redistributed by PFT. Within-cell SOC skill therefore comes only from
   running at 4 km: SOC is the cleanest test of high-resolution modeling, AGB
   measures what fine land cover contributes.
6. **Observational ceiling.** Repeat steps 2–3 between two independent products
   (AGB: ESA CCI vs GEDI L4B or an FIA-based map; SOC: SoilGrids vs gSSURGO).
   Their agreement bounds achievable model skill. Availability of the second
   products has not yet been checked.
7. Secondary targets where matched products exist: forest cover and change,
   burned area (FAREA_BURNED), and regional NBP or flux constraints.
8. Do not count the 30.833°N discontinuity as spatial skill. Do not call the
   0.0708 versus 0.07 historical NBP coincidence a validation.

### D7 (2.7). Disturbance and vulnerability components

ELM's `FIRE` is emitted infrared radiation; `FAREA_BURNED` is burned area
(stored as a rate despite its `proportion` label). Components are reported
and used **separately**; there is no composite index in the main results:

| Component | Definition | Legacy fig05 problem |
|---|---|---|
| Fire | complete column fire C loss (COL_FIRE_CLOSS, or inferred from the NBP identity) ÷ stock, decade mean | used PFT_FIRE_CLOSS, which omits litter/CWD fire |
| Water stress | growing-season mean 1 − BTRAN | annual mean |
| Variability | interannual variability of stock or NBP after detrending | not detrended |

Compute them from the RF run (the managed state at risk); repeat with Default
as a check. They describe modeled exposure, not a project's reversal
probability.

### D8 (2.8). Resolution comparison and uncertainty (Figure 3)

- Compare native 4 km (C), 4 km aggregated to 0.5° (C′), native 0.5° (A) and,
  where it can be built consistently, the downscaled field (B). For a
  downscaled management gain, reconstruct Default and RF separately, with each
  scenario's own PFT fractions, before differencing.
- Report area-weighted distributions, tails, rank agreement and cellwise
  disagreement on common support.
- Headline statistic: the share of area-weighted spatial variance of the
  gain that lies within 0.5° cells, 1 − var(C′)/var(C). Repeat with a band
  around 30.833°N excluded.
- Treat SSP spread, resolution, fire years, the Default choice and structural
  limits as distinct uncertainties; no combined confidence interval without an
  ensemble.

### D9 (2.9). Equal-area prioritization (Figure 5)

**Minimum experiment** (RF − Default, SSP3-7.0, 2091–2100 first):

1. **Eligible land** is fixed before looking at benefits (RF: restorable grass
   plus existing forest; RH: harvested forest; otherwise the common modeled
   land, labelled as a land-screening exercise). Area a(i) = area × landfrac ×
   eligible fraction.
2. **Benefit density** b(i) = period mean of C_RF − C_Default per eligible
   hectare (MgC/ha; 1 gC/m² = 0.01 MgC/ha). Rank by density, not by cell total.
3. **Decision maps.** Fine: b(i). Coarse: B(c) = Σ a(i)b(i) / Σ a(i) over the
   144 fine cells of each 0.5° cell (C′).
4. **Select** the same physical area, 20% and 30% of total eligible area, by
   descending rank. The last coarse cell is taken fractionally (its area and
   total benefit scaled by the fraction), without using hidden 4 km values to
   choose pixels inside it. Ties are broken by a prespecified cell order.
5. **Score both selections on the 4 km field.** Captured benefit
   G = Σ_selected a(i)b(i) (the coarse selection counts every pixel of its
   cells); loss from coarse information = (G_fine − G_coarse)/G_fine; benefit
   per selected hectare; area overlap (both / fine only / coarse only); and
   each vulnerability component's area-weighted mean (reported, not used).
6. **Budget curve.** Repeat for budgets 1–100%; the curves meet at 100%.

**Why scoring favors 4 km:** the fine selection maximizes G on the field used
to score it, so G_fine ≥ G_coarse by construction. The result measures
model-internal information lost through aggregation, not real-world
improvement.

**Vulnerability screen.** Vulnerability constrains which land may be selected;
it is never subtracted from, or weighted against, the benefit (the benefit is
already net of fire, and any weight would be arbitrary).

- **A — report only:** exposure of the potential-only selections (step 5).
- **B — screen, then select:** fix an absolute threshold per component before
  selection (or one value taken from a single shared reference distribution),
  never each resolution's own ranks or median. Remove land above it, then fill
  the same budget by benefit. The coarse side screens with 0.5°-aggregated
  risk, so a coarse cell can pass while containing high-risk pixels; **both
  selections are scored with 4 km benefit and 4 km risk**. Report captured
  benefit, true 4 km exposure, and benefit given up relative to A. If a screen
  leaves less land than the budget, report that rather than relaxing it.
- **C — sensitivity:** repeat B with water stress only (fire has ~0.5°
  effective resolution, A3), and vary each threshold.

**Out-of-sample and comparator tests.** Select with one SSP or window and
score with another (for example SSP2-4.5 2041–2060 → SSP5-8.5 2091–2100);
here the fine selection is no longer guaranteed to win. Repeat with coarse
maps from B (downscaled) and A (native 0.5°), always scoring on the 4 km
field. Vary windows, budgets and eligibility.

---

## Part E — Figures and Results (manuscript §3)

One finding per Results subsection; interpretation proportional to evidence;
values only after the comparison is complete.

### E1. Figure 1 / Results 3.1 — Spatial representation and observational evaluation

**Question:** does 4 km ELM reproduce observed carbon geography, including
variation inside 0.5° cells, beyond what fine land cover explains? Methods D6.

**Panels:** two rows (AGB, 0–30 cm SOC) of observation, 0.5° ELM and 4 km ELM
maps with shared scales; a common-support skill panel; a within-cell anomaly
skill panel showing A, B (AGB), C and the observation ceiling. Downscaled maps
may go to the supplement.

**Interpretation:** report mean-stock accuracy and within-cell pattern
agreement separately; a model can be biased yet place local highs correctly,
or match coarse means while adding wrong detail. Interpret AGB and SOC
independently.

### E2. Figure 2 / Results 3.2 — Regional futures and management benefits

**Question:** how do regional stocks evolve, and how large are the paired
management effects? Methods D3–D5.

**Panels:** compact historical interval plus the four Default SSP
trajectories (36000 s Default, A2); RF − Default and RH − Default for each SSP at both resolutions
(same color per management, line style per resolution), with early/mid/late
summaries; Default − DF in a separate, labelled panel. Full NBP/flux
trajectories go to the supplement.

**Interpretation:** establish magnitudes and the cross-resolution difference
per SSP without presupposing agreement. RF:RH:DF magnitudes are not a ranking
of equally implementable policies.

### E3. Figure 3 / Results 3.3 — Heterogeneity hidden by aggregation

**Question:** where do gains vary within coarse cells, and how much
information does averaging remove? Methods D8. RF is the main example, RH the
consistency check.

**Panels:** RF-gain maps at native 4 km, aggregated 4 km and native 0.5°; one
or two zooms chosen by a predefined rule; an area-weighted cumulative
distribution; the within-cell variance share.

**Interpretation:** the point is how much management-relevant spatial
information aggregation removes, not that the 4 km map looks finer.

### E4. Figure 4 / Results 3.3 — Carbon-pool and process explanations

**Question:** which pools and processes explain the benefits, and what role
does SOC play? Methods D4.

**Analysis specific to this figure:**

- Existing Default stocks versus the **signed** pool changes under RF − Default
  and RH − Default; a large standing SOC pool does not imply a large
  management-induced SOC gain.
- The three-boundary comparison (aboveground, in-situ, + products), including
  whether benefit size, the RF/RH ratio and Figure 5 selections change.
- **RF decomposition**, defined before looking at benefits: cells where RF
  changes land cover (restoration) versus cells where it only stops harvest
  (protection). Report area, benefit and pool response for each; use these
  strata, not post hoc correlations, as the spatial mechanism.
- NEP, land-use/product flux and complete fire loss in the NBP budget, by
  stratum.
- A negative modeled SOC response is a model result for this scenario and
  horizon, not a general empirical claim.

**Panels:** Default pool composition (with products); signed RF/RH pool
contributions; three-boundary benefits; restoration versus protection strata.
The NBP decomposition is one small panel or supplementary.

### E5. Figure 5 / Results 3.4 — Consequences for spatial prioritization

**Question:** given the same physical area budget, does finer information
change where management is prioritized, and at what risk? Methods D9.

**Panels:**

- **Main panel:** an agreement map showing land selected by both approaches,
  by 4 km only and by the coarse approach only.
- Area-budget versus captured-benefit curves, with 20% and 30% marked.
- Captured benefit and true 4 km exposure of both selections at equal area,
  before and after the screen.
- Potential-versus-risk scatter: the horizontal line is the absolute risk
  threshold, the vertical line is the budget cutoff, and the coarse selection
  is shown in its own color.
- Cross-SSP/time overlap heatmap, in the supplement if space is short.

**Relation to the poster siting panel**
(`../carbon_offset_poster/outputs/panel4_siting_RF_4km*.png`). The poster
selected the high-potential/low-vulnerability quadrant with both lines at
domain medians. That is a special case of D9's screen-then-select, in which
both lines sit at the medians. It is not reused as-is:

- The selected area was set by the medians (33.6% at 4 km, 37.4% at 0.5°), so
  captured carbon cannot be compared.
- Vulnerability was rank-normalized within each resolution and split at its
  median, so half the land is always "high risk" and index values differ in
  meaning between resolutions.
- Three components were merged into one index, hiding the driver and carrying
  the HDM artifacts into the map.
- The 0.5° version used the native 0.5° run rather than the aggregated map.

| Poster panel | Use in Figure 5 |
|---|---|
| A benefit map | Keep; recompute from the paper cohort |
| B fire risk map | Replace with separate component maps; supplement or inset |
| C composite vulnerability | Drop from the main result; supplement only if kept |
| D siting quadrants | Replace with the agreement map (main panel) |
| E potential-vs-vulnerability scatter | Keep, with threshold and budget-cutoff lines and the coarse selection marked |
| F quadrant area and mean potential | Replace with equal-area benefit/exposure comparison and the budget curve |

**Interpretation:** the in-sample loss measures model-internal information
removed by aggregation. The out-of-sample tests and the water-only screen show
whether any advantage is stable and where it comes from. The expected value
of resolution is finding high-benefit, low-risk pixels that a coarse average
mixes with poor ones.

---

## Part F — Discussion (manuscript §4)

Each part opens with a result, then explains cause and meaning.

1. **When does higher resolution add credible information?** (Figs 1, 3, 5)
   AGB and SOC skill at common support and within cells; what the downscaled
   field already reproduces; where native 4 km adds or fails to add
   information. AGB skill partly reflects land cover, while within-cell SOC
   skill can only come from running at 4 km.
2. **Why do benefits vary across the landscape?** (Figs 3, 4) Forest
   composition, land-use and harvest change, local conditions and pool
   responses; existing stocks versus management-induced changes. SOC and the
   product-pool boundary together determine what "offset potential" measures.
   The restoration/protection split shows what the RF bundle delivers.
3. **How do disturbance and scenario uncertainty affect priorities?** (Figs 4,
   5) Relation of gains to fire and water stress; screen sensitivity; fire's
   HDM-limited resolution and its lack of SSP-specific ignition; stability
   across SSPs and windows. Indicators are exposure, not reversal
   probabilities.
4. **What do the equal-area results mean for management?** (Fig 5) Locations
   and benefits affected by aggregation; the in-sample advantage of 4 km by
   construction versus out-of-sample stability. Use for regional or
   subregional screening; project selection also needs eligibility,
   ownership, cost and verification. Compare RF/RH per eligible or treated
   hectare before any policy comparison. Credit concepts, in one short
   paragraph: additionality only relative to the modeled Default; permanence
   informed but not quantified; leakage not simulated; credited quantities
   must match the pool and product boundary (Table 2).
5. **Scope and limitations.** Differing 0.5°/4 km configurations and
   spin-ups; driver resolution (Table 1); crit_dayl_stress, the 30.833°N
   discontinuity (still present in the RF/RH pair); one shared soil column and no forest age
   structure; instantaneous DF and bundled RF; unrepresented disturbances
   (insects, windthrow, prescribed burning); observational uncertainty; a
   single model; market feedbacks outside ELM. Separate limitations that
   affect magnitude from those that could change sign or ranking.

---

## Part G — Conclusions and abstract

**Conclusions**, three claims, worded by the completed tests:

1. Which observed patterns 4 km ELM captures, and whether skill improves
   beyond land cover alone.
2. Regional management benefits and their cross-resolution consistency, with
   local heterogeneity and pool pathways shaping where they occur.
3. The measured effect of resolution on equal-area priorities: overlap,
   captured benefit, exposure and stability.

Do not conclude that the simulations quantify marketable credits, or that
climate policy without land management "cannot work".

**Abstract skeleton:**

1. Problem: regional estimates conceal local variation needed for management
   and disturbance screening.
2. Approach: 0.5° and 4 km ELM, four SSPs, Default/RF/RH/DF, observational
   evaluation, aggregated and downscaled comparators.
3. Evaluation result.
4. Regional result (one resolution and window, then cross-resolution
   difference; RF is a bundle, DF an idealized bound).
5. Heterogeneity and process result.
6. Prioritization result, including how much of the 4 km selection the
   downscaled field reproduces.
7. Meaning and limits; not issued credits.

---

## Part H — Tables and supplement

**Main tables**

1. **Simulation matrix and driver resolution**, from the A2 cohort: runs,
   parameter value per run, shared and differing inputs (D1 table).
2. **Accounting definitions and boundaries:** each metric, its equation and
   pools (TOTECOSYSC includes products), the three boundaries, windows,
   interpretation.
3. **Evaluation data and metrics:** products, years, native resolution,
   matching, statistics, and the observation-versus-observation ceiling.

**Supplement:** full 1850–2100 trajectories; CMIP6/TRENDY context; all
scenario and resolution maps; fire evaluation, budgets and component maps;
grid nesting, area conservation and year-completeness QA; daylength and DF
grass diagnostics; pool-closure details; selection sensitivity (thresholds,
windows, eligibility, budgets, comparators, cross-SSP overlap). See also
[supplement/README.md](supplement/README.md).

---

## Part I — Closure checklist and work order

**Before any figure**

1. Update CASE_MATRIX.md and `code/common.py` to the A2 pairing (two Default
   runs per SSP and resolution) and verify completeness and parameters of all
   46 directories.
2. Fix units, masks, windows and the carbon-stock definition (D4, D5); add
   assertions for full-year coverage, identical years/grids, land masking and
   weighted quantiles.

**Analyses, in order**

3. Figure 1 (D6): common-support and within-cell evaluation; confirm the
   second observation products exist.
4. Figures 2–3 (D3–D5, D8): recompute paired benefits and spatial
   distributions from the same cohort.
5. Figure 4 (D4): pool closure with the derived product pool; three-boundary
   test; restoration/protection split and restored versus zero-harvest area;
   process budget.
6. Figure 5 (D9): minimum experiment, then screen, out-of-sample and
   comparator tests.
7. Fire diagnostics: FAREA_BURNED units and meaning; burned area versus carbon
   burned per area; meteorological controls; external comparison if possible.

**Writing order**

8. Tables 1–2 → freeze the five figures with one-sentence findings → Methods
   → Results → Discussion → Introduction and Abstract last.

**Do not carry over:** poster or legacy headline numbers; "future sink under
all SSPs" (the documented 0.5° SSP1-1.9 2024–2100 mean NBP was slightly
negative); a claim that the daylength bias is proven conservative.

---

## Part J — Journal positioning (provisional)

- **Global Biogeochemical Cycles** (current target): resolution-dependent
  heterogeneity linked to carbon-cycle processes and accounting boundaries.
- **Agricultural and Forest Meteorology:** fits only if fire and productivity
  changes are attributed to meteorological controls.
- **Global Change Biology:** after observational evaluation, fire attribution
  and a management × climate result that generalizes beyond one SSP.
