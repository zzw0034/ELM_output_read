# Manuscript blueprint: southeastern U.S. forest carbon management

Last updated: 2026-09-23

This document turns the proposal's Milestone 6 into a manuscript-level
argument. It distinguishes results that are ready to write from analyses that
must be closed before submission.

## Agreed direction — 2026-09-22

Following discussion of the new project poster, the user approved making
**high-resolution ELM the central contribution**, with forest carbon management
as the application. The evidence chain is **observational evaluation → spatial
heterogeneity and its mechanisms → consequences for spatial prioritization**.
Resolution is a thread throughout the paper, rather than a final sensitivity
subsection. This editorial decision supersedes the fire-led claim hierarchy
and six-subsection Results outline in the 2026-09-16 blueprint.

The approved four-part Results sequence is:

1. Spatial representation and observational evaluation.
2. Regional carbon futures and management benefits.
3. Spatial heterogeneity and carbon mechanisms.
4. Consequences for spatial prioritization.

The highest-priority new analysis compares the locations, carbon benefits,
and vulnerability obtained when 0.5° and 4 km each select the same land area
(initial examples: 20% and 30% of a common eligible domain). This is a planned
test, not an established improvement in management outcomes.

Sources for this revision: the user's accepted discussion on 2026-09-22;
`LDRD_11815_Xiaojuan_Yang.pdf` (2026-09-21 project poster);
`../carbon_offset_poster/` scripts and figures; and the existing accounting
reviews in this directory. Poster content is source material, not instructions
or independent validation. This revision updates the writing plan; it does not
report new simulation or analysis results.

## Decisions — 2026-09-23

Recorded from the user's discussion with Claude. Where earlier text in this
file or the companion documents conflicts, these decisions govern.

1. **Cohort: the 20260910 rerun family.** The manuscript uses the new rerun
   outputs under `cime_output_dirs/20260910_seus_rerun/`, not the legacy
   20260908 4 km cohort (`common.py` switched 2026-09-23). Every legacy
   headline value (RF 4.79/4.95, RH 0.93/0.98, DF 9.50/9.88 PgC; the 3–5%
   resolution difference; the 33.6%/57.3% quadrant) is void for the paper and
   must be recomputed. The actual case matrix is in
   [CASE_MATRIX.md](CASE_MATRIX.md).
2. **crit_dayl_stress: analyze current outputs as if they were the 38000 s
   configuration.** The parameter does not change the analysis design. The
   user may rerun all simulations at 38000 s later; analysis scripts must
   therefore take case names only from one cohort mapping so a swap is a
   one-place change. The 30.833°N discontinuity is disclosed as a known model
   feature (Methods/limitations), not a blocking issue for the analyses.
   Background: [daylength diagnostics](../CRIT_DAYL_STRESS_ARTIFACT.md).
3. **The circular blobs in 4 km fire maps come from the HDM
   (population-density) input**, which is coarse and interpolated. ELM's fire
   ignition and suppression terms therefore carry HDM's effective resolution,
   not 4 km. Consequences: report the fire component of vulnerability
   separately; test every selection result with and without it; list HDM in
   the effective-input-resolution table (Methods 2.1).

### Analysis framing adopted for the resolution argument

Every "4 km is better" result is tested against a **downscaled 0.5°** field:
0.5° per-PFT (or per-forest-area) carbon density multiplied by the 4 km PFT
fractions. This separates two sources of apparent improvement:

| Field | What it knows |
|---|---|
| A. native 0.5° | coarse-cell mean only |
| B. downscaled 0.5° | 4 km land cover; 0.5° climate, soil and processes |
| C. native 4 km | 4 km land cover plus 4 km climate, soil and their nonlinear process response |

A→B is the value of high-resolution land-cover input; B→C is the value of
running the model at 4 km. Only B→C supports "high-resolution *modeling*".
The same B field is a comparator in the equal-area selection (Methods 2.9),
where the primary coarse comparator is **4 km aggregated to 0.5°** (same
simulation, so no configuration confound); native 0.5° is secondary.

### Evidence update discovered during directory alignment (2026-09-22)

The September 22
[4 km rerun comparison](../20260908_seus_4km/rerun_comparison/FINDINGS.md)
records the newer outputs, including management cases under all four SSPs,
and their restart/parameter/configuration differences from the legacy
cohort. Configuration differences between the resolutions still have to be
audited before any difference is called a pure grid-spacing effect.

The four-SSP 0.5° paired Default/DF test at 38000 s changed 2024–2100
cumulative NBP avoided-loss benefits by +5.3–5.9%. Under decision 2 this is
the expected order of magnitude of a later full rerun, not a correction
factor to apply. See DF_GRASS_SENSITIVITY.md for the history.

## 1. Recommended scientific story

### Central question

What information does high-resolution land modeling reveal about southeastern
U.S. forest carbon management that regional totals conceal, and how does that
information change estimates of local carbon benefits and priority locations
under future global change?

### One-sentence answer

High-resolution ELM translates broadly similar regional carbon-benefit totals
into spatially differentiated management opportunities by resolving local
heterogeneity in carbon gains and modeled vulnerability. Better observational
agreement and the consequences for equal-area site selection must be tested
before claiming improved real-world decisions.

### Main claim hierarchy

1. **Spatial credibility — to quantify.** The poster's 4 km AGB and SOC maps
   provide an observational comparison. Restore the 0.5° panels and test which
   observed patterns are better represented at 4 km; visual detail alone does
   not establish accuracy.
2. **Regional consistency — to recompute on the new cohort.** The legacy
   cohort gave 3–5% cross-resolution differences in management benefits; that
   value is void (decision 1) until recomputed on the 20260910 rerun.
   Agreement within one model is resolution consistency, not independent
   validation.
3. **Local heterogeneity — partly established.** Fine resolution changes the
   low- and high-potential tails. Explain the within-0.5° variation using
   forest cover, management perturbations, carbon pools, and relevant
   environmental conditions. Attribution remains to be completed.
4. **Spatial prioritization — the key new test.** Quantify whether equal-area
   selections differ in location, modeled benefits, and vulnerability. The
   existing high-potential/low-vulnerability quadrant result supports spatial
   concentration, but does not by itself demonstrate an advantage of 4 km.

Carbon-pool allocation and the NEP/fire/land-use budget support this argument.
Keep fire as a mechanism and vulnerability component; do not make rising fire
the title-level claim before independent evaluation and attribution.

### Language for the primary outcome

Use **modeled additional ecosystem carbon storage** for RF−Default and
RH−Default, and **modeled avoided ecosystem-carbon loss** for Default−DF.
Use “carbon-offset potential” when connecting the result to the proposal or
crediting application, not as a synonym for issued credits. The simulations do
not establish legal additionality, market leakage, durability guarantees, or
credit quantity.

## 2. Working titles

**Approved working title:**

> High-resolution land modeling reveals spatial opportunities for forest
> carbon management in the southeastern United States

Alternative emphasizing the regional-to-local relationship:

> From regional carbon potential to spatial prioritization: high-resolution
> land modeling of southeastern U.S. forest management

Avoid “climate-driven fire losses” until the fire increase has been attributed
to weather/climate rather than fuel, land cover, or forcing artifacts.

## 3. Research questions and testable expectations

### RQ1: Which observed spatial patterns does 4 km ELM capture better?

Compare 0.5° ELM, 4 km ELM, and observations for AGB, SOC, and forest cover.
Test regional bias and common-support skill separately from within-coarse-cell
pattern skill. Improved representation is a hypothesis; the poster's
illustrative maps are not a completed quantitative benchmark. Include the
downscaled 0.5° field (decision framing above) so that skill gained from 4 km
land cover is separated from skill gained by running the model at 4 km.

### RQ2: How consistent are regional futures and management benefits across resolutions?

Use the four Default SSPs to establish the regional baseline, then RF−Default,
RH−Default, and Default−DF for management effects under every SSP for which
both resolutions have matched cases ([CASE_MATRIX.md](CASE_MATRIX.md)).
Distinguish stocks from annual/cumulative NBP, and the DF upper bound from
interventions. Recompute the cross-resolution benefit difference on the new
cohort.

### RQ3: What local variation and carbon processes do regional totals conceal?

Compare native 4 km, area-weighted 4 km aggregated to 0.5°, and native 0.5°.
Quantify distribution tails and within-coarse-cell heterogeneity, and examine
their relationships with land cover, management changes, and environmental
conditions. Separate averaging effects from differences between simulations.
Partition management-induced stock differences and explain the relevant flux
budget. The provisional 66–70% aboveground share requires pool closure.

### RQ4: How does spatial resolution change equal-area prioritization?

Select the same physical land area using each resolution and compare location
overlap, captured carbon benefit, and vulnerability on common support. Test
20% and 30% area budgets plus a broader selection curve, using a common
eligibility mask. Compare potential-only selection with explicitly defined
vulnerability screens. Compare 4 km selections with those from 4 km
aggregated to 0.5° (primary), the downscaled 0.5° field, and native 0.5°. Where
management cases exist for several SSPs, compare selection overlap across SSPs
with overlap across resolutions. A gain from 4 km selection is an outcome to
test, not an assumption or a field-validated benefit.

## 4. Detailed manuscript structure

## 1 Introduction

### Paragraph 1 — scientific and management importance

Introduce southeastern U.S. forests as a large, actively managed carbon system
where regrowth, harvesting, land conversion, and disturbance act on similar
time scales. Connect to climate mitigation, but keep the first paragraph about
the carbon-cycle problem rather than the credibility of voluntary markets.

### Paragraph 2 — the gap between regional budgets and local management

Organize the gap around three scientific choices:

1. **Counterfactual baseline:** additional storage depends on what would have
   happened without management.
2. **Accounting boundary:** standing biomass, ecosystem stocks, NBP, harvested
   products, and avoided loss are different quantities.
3. **Time and spatial scale:** disturbance produces event-driven losses, and
   regional totals can conceal sub-grid heterogeneity relevant to project
   siting.

This framing is stronger than claiming that all crediting studies simply omit
soil carbon. The present results show that standing stocks are mostly outside
aboveground biomass, while management increments are mostly above ground.

Make spatial scale the organizing gap: similar regional totals can arise from
very different local distributions. Managers need the location and variability
of additional carbon and disturbance exposure, not only a regional integral.

### Paragraph 3 — limitations of existing approaches

Review empirical inventory estimates, remote-sensing/static potential maps,
and process-model studies. State exactly which estimates disagree and whether
the disagreement concerns current stocks, biophysical potential, or additional
future storage. Do not use “even the sign is inconsistent” without matching
definitions and spatial/temporal boundaries.

Explain the remaining gap: few studies jointly resolve dynamic land use,
multiple ecosystem pools, disturbance losses, and spatial scale while applying
explicit management counterfactuals.

Use CMIP6/TRENDY as concise regional context, with matched variables, periods,
and scenario definitions. Their spread motivates uncertainty and scale
questions; it does not isolate a resolution effect because the models differ
in many other respects. The main resolution comparison is within ELM.

### Paragraph 4 — approach, objectives, and hypotheses

Introduce ELM at 0.5° and 4 km, four Default SSPs, and the matched management
cohort from the 20260910 rerun ([CASE_MATRIX.md](CASE_MATRIX.md)). End with the
four research questions above. State before the
Results that DF is an idealized bound and RF combines restoration with broader
forest protection/zero harvest.

Preview the evidence chain: evaluate spatial representation, quantify regional
benefits, explain local heterogeneity, and test equal-area prioritization.

## 2 Materials and Methods

### 2.1 Study region and ELM configuration

Define domain, land area, PFT representation, carbon pools, fire module, and
the absence of explicit forest age cohorts. Explain how the grids nest and how
land fraction enters domain integrals.

Document the high-resolution surface-data and land-use forcing workflow and
the corresponding 0.5° aggregation. Identify differences in meteorological
forcing, PFT composition, spin-up, timestep, and other configuration settings.
Where these are not controlled, describe a comparison of model configurations
rather than assigning every difference to grid spacing alone.

Include a table of the **effective resolution of each driver**: meteorology,
surface data/PFT fractions, land-use and harvest forcing, soils, nitrogen
deposition (hard-coded 144×96 in CPL_BYPASS), CO2 (global), and the fire
inputs, notably HDM population density (coarse, interpolated; source of the
circular structures in 4 km fire fields). Only drivers resolved at 4 km can
produce genuine 4 km process structure.

### 2.2 Forcing, spin-up, and historical simulation

Give meteorological forcing source/downscaling, spin-up protocol, transient
period, CO2, nitrogen deposition, land use, and harvest forcing. Report why
the intervention begins in 2024 rather than the proposal's original 2015.

### 2.3 Future and management experiments

Use Table 1 for the actual simulations, not the proposed full factorial design.
Build it from [CASE_MATRIX.md](CASE_MATRIX.md) (20260910 rerun cohort). Explain
any choice of a central SSP. State the crit_dayl_stress value used, and note
that analyses are designed to be rerun unchanged on a 38000 s cohort
(decision 2).

Define RF accurately as a **restoration/protection policy bundle** if it both
restores forest and sets harvest to zero beyond the newly restored area.
Describe DF as instantaneous forest-to-grass conversion with no secondary
succession and RH as the implemented harvest reduction.

### 2.4 Carbon accounting and outcome definitions

This should be the most explicit methods subsection.

Stock outcomes:

```text
Restoration/protection benefit(t) = C_RF(t) - C_Default(t)
Avoided-deforestation bound(t)    = C_Default(t) - C_DF(t)
Reduced-harvest benefit(t)        = C_RH(t) - C_Default(t)
```

State whether `C` is `TOTECOSYSC` and list its included pools. Define the pool
partition separately. Do not treat the sum of selected pools as identical to
`TOTECOSYSC` until the current several-percent residual is closed.

Flux outcomes:

```text
NBP = NEP - COL_FIRE_CLOSS - LAND_USE_FLUX
LAND_USE_FLUX = land-conversion loss + wood-product-pool loss
```

Explain that `WOOD_HARVESTC` transfers carbon to product pools and is not all an
immediate atmospheric emission. State that cumulative NBP is not identical to
the ecosystem stock change when boundaries differ.

### 2.5 Temporal aggregation and spatial integration

Document calendar-aware monthly weighting, complete-year checks, land masks,
cell-area weighting, and PgC conversion. Define the historical comparison
window (2014–2023), future windows, and end-of-century window (2091–2100).
Describe event-year analysis rather than implying monotonic decline.

### 2.6 Model evaluation

Use independent AGB, SOC, forest cover/change, NBP or flux constraints, and
burned-area products with matched years, domains, units, and pool boundaries.
Report bias, RMSE, spatial correlation, and distributional agreement. Do not
call the 0.0708 versus historical 0.07 coincidence a validation.

For the AGB/SOC evaluation, show **0.5° ELM | 4 km ELM | observations**.
Reconcile biomass versus carbon units, land/forest masks, missing data, and
SOC depth. The poster uses 2014–2020 ELM/ESA-CCI means and SoilGrids 0–30 cm;
do not imply SoilGrids is a 2014–2020 time series. Report performance after
aggregation to a common support, then test whether 4 km captures observed
within-0.5° anomalies. A finer-looking map alone is insufficient evidence.
Add the downscaled 0.5° field as a fourth column and report skill for A, B
and C (decision framing above); only the B→C gain is attributable to running
ELM at 4 km. SOC is likely the more discriminating test, because it depends on
soils, hydrology and temperature more than on where forest is.
Do not count the known 30.833°N daylength discontinuity as observed spatial
skill.

### 2.7 Disturbance and vulnerability metrics

Define burned area, PFT fire loss, inferred complete column fire loss, water
stress, and stock variability. Clarify that ELM's `FIRE` field is infrared
radiation; `FAREA_BURNED` is the relevant burned-area field. Describe any
composite index weights as an analyst choice and include sensitivity to those
weights. The fire component inherits the HDM input's coarse structure
(decision 3); report it separately and repeat selections without it.

Fire loss is already included in NBP and must not be subtracted again from the
management benefit. Fire loss per standing stock is an exposure/intensity
metric, not a project reversal probability.

### 2.8 Resolution comparison and uncertainty

Use three representations: native 4 km, 4 km area-weighted to 0.5°, and native
0.5°. Compare regional totals and cellwise disagreement on common support;
use native distributions and within-cell variability to quantify information
lost through aggregation. Report RMS disagreement, rank agreement, weighted
threshold-area fractions, and controls on local variation.

Treat SSP spread, resolution, fire years, baseline choice, and structural
model limitations as distinct uncertainties. Do not combine them into a
statistical confidence interval unless an ensemble supports that operation.

### 2.9 Equal-area spatial prioritization — priority new analysis

Predefine a common eligibility mask and denominator. Initially use the common
modeled land domain if management-specific eligible area is unavailable, and
label it accordingly; do not equate all regional land with feasible restoration
land. RF affects both restored land and existing forests through zero harvest.

1. At each resolution rank eligible land by the same potential metric and
   period. Start with RF `TOTECOSYSC` differences in 2091–2100. Select 20% and
   30% of the same physical eligible area, with an additional area-budget curve.
2. Compare potential-only ranking with ranking under a specified vulnerability
   screen. Use comparable absolute thresholds or a shared reference
   distribution; independently normalized ranks are domain-relative. Report
   when a screen leaves too little eligible land to meet an area budget.
3. Define cutoff-cell/tie treatment before comparison. Fractional area at the
   cutoff can enforce equal budgets analytically; do not use 4 km information
   to preferentially choose pixels within a selected coarse cell.
4. Transfer selections conservatively to common support and compare area
   overlap, captured PgC/share of potential, mean benefit per selected hectare,
   and individual vulnerability components, as well as the composite score.
5. Evaluate both selection masks against the same reference fields. Treat
   evaluation using 4 km outputs as model-internal. Add common-coarse-support
   and alternative-reference checks to reveal dependence on the chosen
   evaluation field; 4 km is not observational ground truth.
6. Test time windows, area budgets, eligibility masks, index weights, and
   thresholds, including a selection without the HDM-affected fire component.
   Link any advantage to independently evaluated spatial patterns.
7. Coarse comparators, in order: 4 km aggregated to 0.5° (same simulation,
   isolates the resolution of the decision map); downscaled 0.5° (tests
   whether high-resolution land cover alone reproduces the 4 km selection);
   native 0.5° (includes configuration and nonlinearity differences).

The legacy 33.6%/57.3% quadrant statistic (void for the paper, decision 1)
motivated this design but is not a substitute for the equal-area comparison. A quadrant threshold and a fixed
land-area budget answer different questions.

## 3 Results

### 3.1 Spatial representation and observational evaluation

Lead with the 0.5°/4 km/observation comparison. Identify the spatial structures
that 4 km represents and quantify where performance improves or deteriorates.
Show both common-support metrics and observed within-coarse-cell variation.
AGB and SOC need separate assessments; do not infer SOC skill from AGB skill.

Include CMIP6/TRENDY as brief context if definitions and periods align. Keep
the historical trajectory compact, establishing the carbon and land-cover
state from which the counterfactuals diverge in 2024. Full trajectories and
multi-model maps can remain supplementary.

### 3.2 Regional carbon futures and management benefits

Establish the future baseline and intervention magnitudes, with both
resolutions shown. Keep stocks, fluxes, and management differences distinct.

Show the four Default SSP cumulative NBP curves, with the exact flux
decomposition in supporting diagnostics. The current 0.5° results give a
future mean NBP range of −0.0019 to 0.0218
PgC/yr, versus 0.0708 PgC/yr in 2014–2023, without presenting the latter as an
observationally validated climatology.

For the existing 0.5° budget diagnostics, complete fire loss rises from 0.0073 to
0.0671–0.0978 PgC/yr. It explains 82–153% of the NBP difference; NEP offsets
part of the decline in SSP2-4.5, SSP3-7.0, and SSP5-8.5. SSP1-1.9 differs
because NEP also declines. Emphasize episodic fire years rather than gradual,
uniform sink saturation. Detailed fire attribution supports the regional
baseline and does not displace the resolution-centered narrative.

Report RF−Default and RH−Default as management effects. Present Default−DF in
a visually separate panel labeled “idealized avoided-loss upper bound.” Give
early-, mid-, and late-century values, not only 2091–2100 means.

Effect sizes must be recomputed on the 20260910 rerun cohort. For orientation
only, the void legacy 2091–2100 values were RF 4.95/4.79, RH 0.98/0.93 and
DF 9.88/9.50 PgC (0.5°/4 km); do not quote them.

Explain the 2024 DF discontinuity as an imposed instantaneous conversion and
temporary transfer into litter/CWD, not gradual deforestation.

Close with the regional comparison of the recomputed cross-resolution
stock-benefit difference. This establishes
the starting point for asking what those similar totals conceal locally.

### 3.3 Spatial heterogeneity and carbon mechanisms

Begin with the three-way native/aggregated comparison and the distribution
tails. Quantify variation within 0.5° cells and the concentration of benefits
within those cells. Relate local differences to forest cover, the management
perturbation, and environmental conditions using reproducible strata or
diagnostics, rather than attributing patterns from maps alone.

Use the stock-versus-increment distinction to explain benefits. Show signed
pool contributions to each management difference. Report the current 66–70%
aboveground share of the management increment only after closing the selected
pool sum versus `TOTECOSYSC` residual.

Discuss the small negative SOC difference under RF/RH as a modeled response,
not as proof that restoration depletes real-world soil carbon. Connect pool
responses to litter inputs, heterotrophic respiration, conversion debris, and
the analysis time horizon where supported.

Compare SSP3-7.0 Default, RF, and RH using the exact budget. RF has higher NEP
and much smaller LAND_USE_FLUX but also larger fire loss. Its maintained NBP is
therefore a net outcome of competing processes, not evidence that restoration
removes fire risk.

For RF versus Default, the current 0.5°, 2024–2100 mean annual differences are
approximately:

- lower land-use/product loss: +0.0581 PgC/yr;
- higher NEP: +0.0287 PgC/yr;
- higher fire loss: −0.0193 PgC/yr.

These regional flux diagnostics explain the net benefit, but do not alone
attribute within-cell heterogeneity. Complete the spatial diagnostics before
making local causal claims.

### 3.4 Consequences for spatial prioritization

First show individual potential and vulnerability components; then show the
classification. Report the share of total potential retained under a clearly
defined low-risk screen. Use absolute thresholds or show sensitivity to the
domain-median thresholds.

The poster's legacy 4 km RF quadrant (33.6% of land, 57.3% of potential) is
void for the paper; recompute any quadrant statistic on the new cohort after
harmonizing the vulnerability diagnostics. A quadrant is the intersection of
two classes, not the entire low-vulnerability half of the domain.

Make the equal-area comparison the culminating result: for the same 20% or
30% area budget, where do the selections agree or disagree, how much modeled
carbon do they capture, and what vulnerability do they carry? Present the
selection curve and reference-field sensitivity alongside the maps. Report
similar or mixed outcomes if that is what the test finds.

Conclude at the level of subregional screening and management prioritization;
4 km does not resolve ownership parcels or individual forest stands.

## 4 Discussion

### 4.1 What high-resolution modeling adds to forest carbon management

Organize the discussion around three levels of evidence: observational spatial
skill, heterogeneity concealed by regional totals, and consequences for
equal-area prioritization. Explain where averaging removes useful information
and where the two configurations give consistent guidance. Distinguish
model-internal selection gains from independently demonstrated accuracy.
Keep 4 km's role at subregional screening, not parcel-level implementation.

### 4.2 Management ranking is conditional on the counterfactual

The 10:5:1 ranking does not compare three equally realistic policies. DF is a
maximum avoided-loss experiment; RF is a bundled intervention; RH is a
smaller perturbation. Discuss marginal benefit per hectare or per unit forest
area before making cost or policy comparisons.

### 4.3 Carbon-pool boundaries change what “offset potential” means

Use the stock-versus-increment result to explain why large soil stocks do not
imply large soil contributions to near-century management benefits. Relate the
finding to monitoring practice without asserting that a specific protocol
omits a fixed percentage unless protocol evidence supports it.

### 4.4 Disturbance and uncertainty in spatial prioritization

State that the reported management benefits are already net of simulated fire.
Discuss the rise in complete fire loss, event-driven NBP reversals, and the
greater RF fire exposure. Verify which fire processes are represented by the
actual configuration before matching to observations. Discuss prescribed
burning and unrepresented disturbances such as insects and windthrow, and
the absence of project-level reversal probabilities. Explain how index
weights, thresholds, and evaluation windows affect priority-area stability.

### 4.5 Implications for carbon-credit concepts

- **Additionality:** quantified only relative to the modeled Default baseline.
- **Permanence:** informed by event-driven losses, but no contractual durability
  or reversal probability is estimated.
- **Leakage:** not simulated; regional harvest displacement and market effects
  remain outside the system boundary.
- **Measurement:** stock and flux definitions must match the credited pool and
  product-pool boundary.

### 4.6 Limitations and generality

Discuss the single-patch PFT representation, missing forest age structure,
instantaneous DF conversion, RF intervention bundling, grass phenology concern,
fire evaluation and HDM-driven fire structure, prescribed burning,
crit_dayl_stress and the 30.833°N discontinuity, management-SSP coverage,
configuration differences between resolutions, reference-field dependence in
selection tests, and lack of economic/market feedback. Separate limitations
that affect magnitude from those that could change the sign or ranking.

## 5 Conclusions

Use three claims, with wording conditional on the completed tests:

1. State which observed spatial patterns high-resolution ELM captures and
   whether quantitative skill improves relative to 0.5°.
2. Management adds or retains substantial modeled carbon with broadly similar
   regional benefits across resolutions, while local heterogeneity and carbon
   pathways shape the spatial distribution of those benefits.
3. State the measured effect of resolution on equal-area prioritization,
   including location overlap, captured benefits, and vulnerability. Claim
   improved screening only to the extent supported by those tests.

Avoid concluding that the simulations directly quantify marketable credits or
that climate policy without land management “cannot work.”

## 6. Main figures and tables

### Main figures

1. **Spatial credibility (Results 3.1).** 0.5° ELM, 4 km ELM, and observations
   for AGB/SOC, with common-support skill and within-cell pattern metrics.
   CMIP6/TRENDY is a compact context panel or supplementary figure, not a
   substitute for the within-ELM resolution comparison.
2. **Regional futures and management benefits (3.2).** Compact four-SSP NBP
   context plus RF/RH stock-benefit trajectories and a separately scaled DF
   upper-bound panel. Compare both resolutions and early/mid/late horizons.
3. **Heterogeneity hidden by aggregation (3.3).** Native 4 km, aggregated 4 km,
   and native 0.5°; weighted distribution tails, within-cell variation, and
   representative subregions selected by a reproducible rule.
4. **Carbon mechanisms (3.3).** Signed pool contributions and a concise
   NEP/fire/LAND_USE_FLUX management-difference budget. Show spatial strata
   where they explain the heterogeneity in Figure 3; close pool residuals
   before finalizing numerical shares.
5. **Consequences for prioritization (3.4).** Potential/vulnerability and
   selection-agreement maps; captured-benefit versus selected-area curves;
   equal-area overlap and vulnerability comparisons at 20% and 30%.

Five main figures are the working target. Detailed fire maps and baseline
budget/event diagnostics belong in the supplement unless essential to a main
claim. Split a figure only if the combined panels become unreadable; preserve
the four-part Results argument.

### Main tables

1. **Actual simulation matrix and interventions.** Include resolution,
   scenario, intervention, years, forcing, and purpose.
2. **Accounting definitions and system boundaries.** Stock/flux metric,
   equation, included pools, time window, and interpretation.
3. **Evaluation datasets and metrics.** Product, years, native resolution,
   matching procedure, and performance statistics.

### Supplement

- Full 1850–2100 trajectories and proposal time-slice maps.
- Full CMIP6/TRENDY context, with matched quantities and scenario definitions.
- All scenario and resolution maps.
- Fire evaluation, budget/event diagnostics, and vulnerability components.
- Grid nesting, area conservation, calendar/year completeness, and cache QA.
- DF grass-phenology diagnostics and pool-closure analysis.
- Selection sensitivity to thresholds, weights, periods, eligibility, area
  budgets, and evaluation reference fields.

## 7. Analyses that must be closed before submission

### Required for the agreed high-resolution argument

1. Quantify 0.5° versus 4 km observational skill for AGB/SOC and relevant land
   cover, including common-support comparison and within-coarse-cell patterns.
   The poster comparison script explicitly calls its maps illustrative; a
   formal depth/mask/unit-reconciled benchmark remains to be completed.
2. Add the equal-area 20%/30% prioritization experiment from Methods 2.9,
   plus area-budget curves, overlap metrics, and alternative-reference checks.
3. Explain within-cell heterogeneity and distribution tails using land cover,
   management perturbations, and relevant process diagnostics. Separate the
   loss due to aggregation from differences between model configurations.
4. Audit cross-resolution forcing, PFT inputs, spin-up, timesteps, masks, and
   area conservation before describing differences as a resolution effect.
5. Test vulnerability weights, thresholds, and periods; distinguish PFT fire
   loss from complete column fire loss, and assess effects on site rankings.

### Accounting and physical-evidence requirements

1. Independent AGB, SOC, forest-cover, and fire/burned-area evaluation with
   matched domains, periods, and definitions.
2. Resolve the several-percent mismatch between `TOTECOSYSC` and the selected
   pool sum before publishing pool shares.
3. Diagnose the fire increase with `FAREA_BURNED`, fuel/stock variables, and
   meteorological controls; distinguish burned-area effects from carbon burned
   per unit area.
4. Verify the units and source-code meaning of `FAREA_BURNED`, and independently
   test inferred `COL_FIRE_CLOSS` in a targeted output run if feasible.
5. Disclose the daylength mechanism and cite the paired 0.5° Default/DF
   38000 s result as the expected size of a full rerun (decision 2); keep all
   scripts cohort-swappable. Do not claim the bias is proven conservative.
6. Quantify RF's restored area versus the larger area affected by zero harvest;
   do not label the combined response as pure reforestation.
7. Add assertions for full-year coverage, identical scenario years/grids, land
   masking, and weighted quantiles.
8. Do not reuse poster headline numbers (RF 5.9, DF 10.1 PgC) or the legacy
   4.79/4.95 and 9.50/9.88 PgC; recompute on the new cohort with the variable,
   window and stock/flux boundary stated. Do not
   carry over “future sink under all SSPs”: the documented 0.5° SSP1-1.9
   2024–2100 mean NBP is slightly negative. A positive cumulative value that
   includes history does not establish a future-period sink.

### Needed for stronger generality

1. Use the additional-SSP management experiments in the new cohort where
   both resolutions have matched cases (CASE_MATRIX.md); check inventory
   before proposing new simulations.
2. Compare simulated fire changes with an external projection ensemble or
   observationally constrained range.
3. Add a project-relevant metric such as benefit per eligible/restored hectare,
   while avoiding economic claims without cost data.

## 8. Journal-specific emphasis

These are provisional positioning notes carried forward from the earlier
discussion, not a fresh assessment of journal scopes or requirements.

### Global Biogeochemical Cycles — provisional target

Connect high-resolution spatial heterogeneity to carbon-cycle processes,
accounting boundaries, and regional-to-local inference. Figure 4 supplies
the process explanation for the spatial and prioritization results; the
high-resolution argument remains central throughout.

### Agricultural and Forest Meteorology

This becomes a stronger fit only if the fire and productivity changes are
attributed to meteorological controls such as VPD, soil moisture, temperature,
precipitation timing, and fuel moisture. A paper that merely uses climate
forcing but centers on scenario carbon totals is less aligned.

### Global Change Biology

A plausible higher target after observational evaluation, fire attribution,
and at least one additional management×climate test establish a general result
beyond one region and one management SSP.

## 9. Abstract skeleton

1. **Problem:** Regional forest carbon estimates can conceal local variation
   needed for spatial management and disturbance screening.
2. **Approach:** Evaluate ELM at 0.5° and 4 km against AGB/SOC observations;
   analyze four Default SSPs and the matched management cohort of the
   20260910 rerun; compare spatial heterogeneity and equal-area
   prioritization against aggregated and downscaled coarse comparators.
3. **Evaluation result:** Insert measured changes in spatial skill and the
   patterns they concern. No improvement percentage is available yet.
4. **Regional result:** Report management benefits using one resolution and
   time window consistently, then the recomputed cross-resolution
   differences. Label RF as restoration/protection and DF as an upper bound.
5. **Local/process result:** Quantify heterogeneity concealed by aggregation,
   with carbon-pool/flux explanations supported by the completed diagnostics.
6. **Prioritization result:** Insert measured equal-area overlap, benefit, and
   vulnerability differences, including how much of the 4 km selection the
   downscaled 0.5° field reproduces.
7. **Meaning:** Explain what high-resolution modeling adds to subregional
   forest carbon screening, bounded by observational skill, modeled
   counterfactuals, and uncertainty. These estimates are not issued credits.

## 10. Recommended writing order

1. Finalize Table 1 (actual runs and cross-resolution configuration differences)
   and Table 2 (accounting boundaries); reconcile poster headline numbers.
2. Prioritize quantitative spatial evaluation and the equal-area selection
   experiment, alongside pool closure and required fire/DF/RF diagnostics.
3. Freeze the five main figures and their one-sentence conclusions after
   distinguishing established findings from hypotheses still under test.
4. Write Methods from the frozen definitions and scripts.
5. Write Results figure by figure, with one finding per subsection.
6. Write Discussion around the three levels of high-resolution evidence:
   observed spatial skill, local heterogeneity, and prioritization consequences;
   integrate counterfactuals, pool boundaries, and disturbance as explanations.
7. Write Introduction and Abstract last so they describe the evidence actually
   retained in the paper.
