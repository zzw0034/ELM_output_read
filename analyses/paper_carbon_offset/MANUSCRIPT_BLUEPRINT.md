# Manuscript blueprint: southeastern U.S. forest carbon management

Last updated: 2026-09-16

This document turns the proposal's Milestone 6 into a manuscript-level
argument. It distinguishes results that are ready to write from analyses that
must be closed before submission.

## 1. Recommended scientific story

### Central question

How much additional ecosystem carbon can forest restoration/protection and
reduced harvest retain in the southeastern United States under future global
change, and how do disturbance, carbon-pool boundaries, and model resolution
change that estimate and its spatial implementation?

### One-sentence answer

ELM projects large but intervention-specific carbon benefits: restoration and
protection can sustain regional carbon storage as fire losses increase, while
the estimated regional totals are comparatively insensitive to grid spacing
and the locations selected for projects are not.

### Main claim hierarchy

1. Default future scenarios retain far less net carbon than a constant
   2014–2023 sink-rate benchmark, primarily because simulated fire losses rise,
   not because NEP consistently declines.
2. Under SSP3-7.0, restoration/protection, avoided deforestation, and reduced
   harvest produce clearly different additional or retained ecosystem-carbon
   trajectories. Avoided deforestation is an idealized upper bound rather than
   a deployable management estimate.
3. Management-induced carbon increments differ fundamentally from standing
   stock composition: 66–70% of the simulated intervention increment is above
   ground even though most standing ecosystem carbon is outside aboveground
   biomass.
4. Fine resolution changes project screening and the tails of the spatial
   distribution much more than it changes regional totals.
5. Carbon potential and simulated vulnerability are spatially structured, so
   site selection can retain much of the regional benefit while avoiding the
   highest-risk areas. This claim remains conditional on validating the fire
   and vulnerability diagnostics.

### Language for the primary outcome

Use **modeled additional ecosystem carbon storage** for RF−Default and
RH−Default, and **modeled avoided ecosystem-carbon loss** for Default−DF.
Use “carbon-offset potential” when connecting the result to the proposal or
crediting application, not as a synonym for issued credits. The simulations do
not establish legal additionality, market leakage, durability guarantees, or
credit quantity.

## 2. Working titles

Recommended, especially for Global Biogeochemical Cycles:

> Forest management sustains southeastern U.S. carbon storage despite rising
> simulated fire losses

Title emphasizing the scale result:

> Forest carbon benefits are robust regionally but resolution-sensitive for
> project siting in the southeastern United States

More conservative title while fire evaluation remains incomplete:

> Management, disturbance, and spatial resolution shape modeled forest carbon
> benefits in the southeastern United States

Avoid “climate-driven fire losses” until the fire increase has been attributed
to weather/climate rather than fuel, land cover, or forcing artifacts.

## 3. Research questions and testable expectations

### RQ1: What happens without the three management interventions?

Compare four Default SSP simulations. Report stocks separately from annual and
cumulative NBP. Test whether lower future NBP is associated with NEP, complete
column fire loss, or LAND_USE_FLUX.

Expectation supported by current results: complete fire loss is the dominant
budget term behind the difference from the recent historical NBP rate; NEP
increases in SSP2-4.5, SSP3-7.0, and SSP5-8.5 and decreases in SSP1-1.9.

### RQ2: How much carbon does each management counterfactual add or retain?

Under SSP3-7.0, calculate RF−Default, Default−DF, and RH−Default through time.
Distinguish deployable interventions from the DF upper-bound experiment.

Expectation supported by current results: end-of-century effect sizes rank
DF upper bound > RF policy bundle > RH, approximately 10:5:1 in PgC.

### RQ3: Which pools and fluxes produce those benefits?

Partition the management-induced difference rather than only the standing
stock. Keep stock and flux accounting in separate panels and reconcile their
different system boundaries.

Expectation supported by current results: aboveground biomass supplies about
two thirds of each intervention increment, while RF and RH produce small
negative SOC differences by 2100.

### RQ4: How persistent and spatially actionable are the benefits?

Quantify burned area and complete fire-carbon loss, then combine potential and
validated vulnerability components to identify locations with high potential
and lower modeled risk.

Expectation requiring validation: a low-risk subset retains a disproportionate
share of the regional restoration benefit.

### RQ5: What does 4 km resolution change?

Compare native 4 km fields, area-weighted 4 km fields aggregated to 0.5°, and
native 0.5° fields. Separate total-domain differences from changes in the
distribution tails and site ranking.

Expectation supported by current results: total benefits differ by roughly
3–5%, whereas low- and high-potential land fractions differ materially.

## 4. Detailed manuscript structure

## 1 Introduction

### Paragraph 1 — scientific and management importance

Introduce southeastern U.S. forests as a large, actively managed carbon system
where regrowth, harvesting, land conversion, and disturbance act on similar
time scales. Connect to climate mitigation, but keep the first paragraph about
the carbon-cycle problem rather than the credibility of voluntary markets.

### Paragraph 2 — why estimates differ

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

### Paragraph 3 — limitations of existing approaches

Review empirical inventory estimates, remote-sensing/static potential maps,
and process-model studies. State exactly which estimates disagree and whether
the disagreement concerns current stocks, biophysical potential, or additional
future storage. Do not use “even the sign is inconsistent” without matching
definitions and spatial/temporal boundaries.

Explain the remaining gap: few studies jointly resolve dynamic land use,
multiple ecosystem pools, disturbance losses, and spatial scale while applying
explicit management counterfactuals.

### Paragraph 4 — approach, objectives, and hypotheses

Introduce ELM at 0.5° and 4 km, four Default SSPs, and three SSP3-7.0 management
experiments. End with the five research questions above. State before the
Results that DF is an idealized bound and RF combines restoration with broader
forest protection/zero harvest.

## 2 Materials and Methods

### 2.1 Study region and ELM configuration

Define domain, land area, PFT representation, carbon pools, fire module, and
the absence of explicit forest age cohorts. Explain how the grids nest and how
land fraction enters domain integrals.

### 2.2 Forcing, spin-up, and historical simulation

Give meteorological forcing source/downscaling, spin-up protocol, transient
period, CO2, nitrogen deposition, land use, and harvest forcing. Report why
the intervention begins in 2024 rather than the proposal's original 2015.

### 2.3 Future and management experiments

Use Table 1 for the actual simulations, not the proposed full factorial design.
Show four Default SSPs and the three management cases available only for
SSP3-7.0. Explain the a priori reason for selecting SSP3-7.0.

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

### 2.7 Disturbance and vulnerability metrics

Define burned area, PFT fire loss, inferred complete column fire loss, water
stress, and stock variability. Clarify that ELM's `FIRE` field is infrared
radiation; `FAREA_BURNED` is the relevant burned-area field. Describe any
composite index weights as an analyst choice and include sensitivity to those
weights.

Fire loss is already included in NBP and must not be subtracted again from the
management benefit. Fire loss per standing stock is an exposure/intensity
metric, not a project reversal probability.

### 2.8 Resolution comparison and uncertainty

Compare 4 km and 0.5° only after area-weighted aggregation to a common support.
Report regional totals, RMS disagreement, rank agreement, threshold-area
fractions, and overlap of selected top-priority locations.

Treat SSP spread, resolution, fire years, baseline choice, and structural
model limitations as distinct uncertainties. Do not combine them into a
statistical confidence interval unless an ensemble supports that operation.

## 3 Results

### 3.1 Evaluation and historical context

Lead with independent evaluation. Follow with only the historical facts needed
to understand the initial state: forest-area minimum, regrowth, current stock,
and recent NBP. The 1850–2023 abandonment/regrowth trajectory is useful context
but should not become a separate narrative unless observations support it.

Proposed closing sentence:

> These historical simulations establish the initial carbon and land-cover
> state from which all future counterfactuals diverge in 2024.

### 3.2 Default futures lose most of the recent net sink rate

Show the four Default SSP cumulative NBP curves and the exact flux
decomposition. Report that future mean NBP ranges from −0.0019 to 0.0218
PgC/yr, versus 0.0708 PgC/yr in 2014–2023, without presenting the latter as an
observationally validated climatology.

The main mechanistic result is that complete fire loss rises from 0.0073 to
0.0671–0.0978 PgC/yr. It explains 82–153% of the NBP difference; NEP offsets
part of the decline in SSP2-4.5, SSP3-7.0, and SSP5-8.5. SSP1-1.9 differs
because NEP also declines. Emphasize episodic fire years rather than gradual,
uniform sink saturation.

### 3.3 Management produces distinct additional-carbon trajectories

Report RF−Default and RH−Default as management effects. Present Default−DF in
a visually separate panel labeled “idealized avoided-loss upper bound.” Give
early-, mid-, and late-century values, not only 2091–2100 means.

Use the current end-century numbers as effect sizes:

- RF bundle: 4.95 PgC at 0.5° and 4.79 PgC at 4 km.
- RH: 0.98 and 0.93 PgC.
- DF upper bound: 9.88 and 9.50 PgC.

Explain the 2024 DF discontinuity as an imposed instantaneous conversion and
temporary transfer into litter/CWD, not gradual deforestation.

### 3.4 Carbon increments are mostly above ground, unlike standing stocks

Make the stock-versus-increment distinction the organizing result. Show signed
pool contributions to each management difference. Report the current 66–70%
aboveground share of the management increment only after closing the selected
pool sum versus `TOTECOSYSC` residual.

Discuss the small negative SOC difference under RF/RH as a modeled response,
not as proof that restoration depletes real-world soil carbon. Connect pool
responses to litter inputs, heterotrophic respiration, conversion debris, and
the analysis time horizon where supported.

### 3.5 Management can sustain NBP despite greater fire exposure

Compare SSP3-7.0 Default, RF, and RH using the exact budget. RF has higher NEP
and much smaller LAND_USE_FLUX but also larger fire loss. Its maintained NBP is
therefore a net outcome of competing processes, not evidence that restoration
removes fire risk.

For RF versus Default, the current mean annual differences are approximately:

- lower land-use/product loss: +0.0581 PgC/yr;
- higher NEP: +0.0287 PgC/yr;
- higher fire loss: −0.0193 PgC/yr.

This result links the management and disturbance parts of the manuscript.

### 3.6 High-potential, lower-risk areas and resolution sensitivity

First show individual potential and vulnerability components; then show the
classification. Report the share of total potential retained under a clearly
defined low-risk screen. Use absolute thresholds or show sensitivity to the
domain-median thresholds.

End with the resolution result: regional management totals differ by only
3–5%, but the fractions of land in the low and high tails and the identity of
candidate locations differ substantially. This provides the practical reason
for the 4 km simulations.

## 4 Discussion

### 4.1 Management ranking is conditional on the counterfactual

The 10:5:1 ranking does not compare three equally realistic policies. DF is a
maximum avoided-loss experiment; RF is a bundled intervention; RH is a
smaller perturbation. Discuss marginal benefit per hectare or per unit forest
area before making cost or policy comparisons.

### 4.2 Carbon-pool boundaries change what “offset potential” means

Use the stock-versus-increment result to explain why large soil stocks do not
imply large soil contributions to near-century management benefits. Relate the
finding to monitoring practice without asserting that a specific protocol
omits a fixed percentage unless protocol evidence supports it.

### 4.3 Disturbance constrains persistence but is not a reversal probability

State that the reported management benefits are already net of simulated fire.
Discuss the rise in complete fire loss, event-driven NBP reversals, and the
greater RF fire exposure. Limit inference to wildfire represented by ELM;
prescribed burning, insects, windthrow, and project-level reversal probabilities
are not represented.

### 4.4 Resolution matters for decisions more than regional budgets

Explain averaging and loss of distribution tails. Connect this to screening,
monitoring, and environmental heterogeneity. Do not claim that 4 km resolves
individual projects; 4 km is still much coarser than ownership parcels and
forest stands.

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
fire evaluation, prescribed burning, management cases under only SSP3-7.0,
and lack of economic/market feedback. Separate limitations that affect
magnitude from those that could change the sign or ranking.

## 5 Conclusions

Use three claims only:

1. Rising simulated fire losses strongly reduce future net carbon uptake in
   the Default simulations, even where NEP rises.
2. Active forest management adds or retains substantial ecosystem carbon, but
   the magnitude depends on the counterfactual and carbon-accounting boundary.
3. High resolution adds most value for locating projects and characterizing
   heterogeneity rather than revising the regional total.

Avoid concluding that the simulations directly quantify marketable credits or
that climate policy without land management “cannot work.”

## 6. Main figures and tables

### Main figures

1. **Model evaluation and historical initial state.** Observed-versus-modeled
   AGB/SOC/fire metrics plus a compact 1850–2023 forest-area/carbon trajectory.
2. **Why the Default sink weakens.** Cumulative NBP for four SSPs and a source-
   exact NEP/fire/LAND_USE_FLUX decomposition, including fire-event years.
3. **Management effect trajectories.** RF and RH primary panels; DF as a
   separately scaled, explicitly labeled upper-bound panel; both resolutions.
4. **Signed carbon-pool contributions.** Management-induced increments through
   time, distinguishing aboveground, roots, dead pools, and SOC; include the
   closure residual until resolved.
5. **Potential and vulnerability.** A limited set of maps plus the amount of
   total potential retained under risk screens; keep component maps available.
6. **Resolution consequence.** Regional totals, common-support comparison,
   distribution tails, and overlap of selected locations.

Fire maps can be a seventh main figure only after observational evaluation;
otherwise put the full fire diagnostics in the supplement and retain the NBP
budget panel in Figure 2.

### Main tables

1. **Actual simulation matrix and interventions.** Include resolution,
   scenario, intervention, years, forcing, and purpose.
2. **Accounting definitions and system boundaries.** Stock/flux metric,
   equation, included pools, time window, and interpretation.
3. **Evaluation datasets and metrics.** Product, years, native resolution,
   matching procedure, and performance statistics.

### Supplement

- Full 1850–2100 trajectories and proposal time-slice maps.
- All scenario and resolution maps.
- Fire and vulnerability components and weight sensitivity.
- Grid nesting, area conservation, calendar/year completeness, and cache QA.
- DF grass-phenology diagnostics and pool-closure analysis.
- Additional thresholds and spatial overlap metrics.

## 7. Analyses that must be closed before submission

### Required for either GBC or AFM

1. Independent AGB, SOC, forest-cover, and fire/burned-area evaluation with
   matched domains, periods, and definitions.
2. Resolve the several-percent mismatch between `TOTECOSYSC` and the selected
   pool sum before publishing pool shares.
3. Diagnose the fire increase with `FAREA_BURNED`, fuel/stock variables, and
   meteorological controls; distinguish burned-area effects from carbon burned
   per unit area.
4. Verify the units and source-code meaning of `FAREA_BURNED`, and independently
   test inferred `COL_FIRE_CLOSS` in a targeted output run if feasible.
5. Complete the DF converted-gridcell phenology check and determine whether the
   grass issue can materially change Default−DF.
6. Quantify RF's restored area versus the larger area affected by zero harvest;
   do not label the combined response as pure reforestation.
7. Add assertions for full-year coverage, identical scenario years/grids, land
   masking, and weighted quantiles.

### Needed for stronger generality

1. Management experiments under at least one additional SSP, or explicitly
   narrow all management conclusions to SSP3-7.0.
2. Compare simulated fire changes with an external projection ensemble or
   observationally constrained range.
3. Test vulnerability-index weights and absolute thresholds.
4. Add a project-relevant metric such as benefit per eligible/restored hectare,
   while avoiding economic claims without cost data.

## 8. Journal-specific emphasis

### Global Biogeochemical Cycles — recommended current target

Center the paper on the carbon budget: stock-versus-flux boundaries, carbon-
pool allocation, fire losses, product-pool losses, and scale dependence. Make
Figure 2's exact NBP decomposition and Figure 4's pool mechanisms central.

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

1. **Problem:** Estimates of forest mitigation depend on the assumed baseline,
   carbon pools, disturbance, and spatial scale.
2. **Approach:** ELM simulations at 0.5° and 4 km quantify four Default SSPs and
   three SSP3-7.0 management counterfactuals across ecosystem pools and fluxes.
3. **Baseline result:** Future mean NBP is much lower than the 2014–2023 model
   mean because complete fire losses rise, despite higher NEP in three SSPs.
4. **Management result:** End-century modeled benefits are approximately 4.9
   PgC for RF, 1.0 PgC for RH, and 9.7 PgC for the idealized DF avoided-loss
   bound, with 66–70% of increments above ground after pool closure is verified.
5. **Scale/risk result:** Regional benefits agree within several percent across
   resolutions, while fine resolution changes the tails and candidate-site
   classification.
6. **Meaning:** Process-aware, spatially explicit baselines are necessary to
   translate regional forest-carbon potential into credible management
   estimates; these estimates are not themselves marketable credits.

## 10. Recommended writing order

1. Finalize Table 1 (actual runs) and Table 2 (accounting boundaries).
2. Close evaluation, pool residual, RF bundling, DF phenology, and fire
   attribution.
3. Freeze the six main figures and their one-sentence conclusions.
4. Write Methods from the frozen definitions and scripts.
5. Write Results figure by figure, with one finding per subsection.
6. Write Discussion around counterfactuals, pool boundaries, disturbance, and
   resolution.
7. Write Introduction and Abstract last so they describe the evidence actually
   retained in the paper.
