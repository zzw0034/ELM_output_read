# Manuscript figure, results, and discussion plan

Updated: 2026-09-24

This is a working analysis and writing plan for the southeastern U.S. forest-carbon manuscript. It is the **only** place the figure-by-figure Results and the Discussion structure are maintained; [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) keeps the Introduction, Methods, tables and closure checklist. It summarizes the current discussion; it does not report newly calculated results. Use the final, consistently configured simulation cohort and recompute all numbers before writing quantitative claims. The experiment inventory is in [CASE_MATRIX.md](CASE_MATRIX.md); the broader manuscript plan is in [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md).

## 1. Scientific argument

The central contribution is **high-resolution ELM**, with forest carbon management as the application. The evidence should proceed in this order:

1. Test spatial patterns against observation-based estimates.
2. Establish regional carbon trajectories and modeled management benefits.
3. Quantify spatial heterogeneity and explain its carbon-pool and process contributions.
4. Test whether that information changes equal-area management priorities.

The Introduction has one organizing gap: coarse or regional carbon estimates do not show where management yields the largest modeled benefit at acceptable modeled disturbance exposure, and it is largely untested whether resolving that heterogeneity changes equal-area priorities. Two related issues are introduced briefly as context, not as separate gaps: which pools an accounting boundary includes (soil, products), and disturbance risk to persistence. Do not assert that crediting studies generally omit soil carbon (see blueprint Introduction paragraph 2). The paper tests the spatial consequences of these issues; it does not quantify issued credits or project-level reversal probabilities. Disagreement among SOC data products is relevant to uncertainty, but is not a separate central research question here.

## 2. Shared definitions for all figures

- Use **Default** for the reference scenario. Report RF − Default and RH − Default as modeled additional ecosystem carbon storage. Report Default − DF as an idealized avoided-loss bound.
- RF combines restoration and forest protection/zero harvest beyond newly restored land. RH reduces harvest. DF is an idealized forest-to-grass conversion experiment. Their total Pg C values are not a ranking of equally implementable policies.
- Use the same SSP, time window, carbon variable, land mask, and physical area definition within each paired comparison. Distinguish a carbon **stock difference** from annual or cumulative NBP.
- Use TOTECOSYSC for the primary stock benefit. In this ELM version **TOTECOSYSC = TOTVEGC + CWDC + TOTLITC + TOTSOMC + TOTPRODC**, i.e. it includes the wood/crop product pools (blueprint Methods 2.4). Call it ecosystem-and-product carbon, or define it on first use. TOTPRODC is not in our h0 output; derive it as the residual of TOTECOSYSC. Close pool contributions against TOTECOSYSC with this product term before reporting percentage shares.
- Fire losses are already represented in the modeled net carbon outcome. A risk screen may constrain site selection, but fire losses must not be subtracted from the stock benefit a second time.
- The native 0.5° and 4 km runs differ in spatial inputs and spin-up histories. A difference between them cannot automatically be attributed to grid spacing alone. Aggregating one 4 km simulation to 0.5° isolates information lost by spatial averaging.
- The current 20260910 case matrix records four SSPs with Default, RF, RH, and DF at both resolutions. Existing poster and legacy figure numbers must not be carried into the manuscript as updated results.

## 3. Five main figures and corresponding Results

### Figure 1 / Results 3.1 — Spatial representation and observational evaluation

**Question:** Does 4 km ELM reproduce observed forest-carbon geography, including variation inside a 0.5° cell?

**Analysis**

1. Match the AGB comparison to verified observation years and carbon units. Match SOC to the same soil depth, initially 0–30 cm. Use the same valid forest/land mask and area denominator for all compared fields.
2. Aggregate observation-based maps and the 4 km simulation to common 0.5° support. Compare both ELM resolutions with the observation-based estimate using signed bias, RMSE, spatial correlation, and distributions.
3. Separately evaluate fine-scale patterns inside coarse cells. First aggregate observations to the 4 km support. For every coarse cell c, subtract the observation mean of its valid fine cells from each fine observation, and subtract the 4 km model mean of the same cells from each model value. These are **two anomaly fields**, one observed and one simulated. Compare their spatial correlation, RMSE, and variation amplitude across the common valid cells.
4. At this within-cell scale, a native 0.5° field is constant and has zero anomalies. Compare the 4 km anomalies with that flat baseline and, for AGB, with a coarse model field downscaled using fine-resolution vegetation fractions. This tests whether fine land cover alone explains the pattern.
5. **Observational ceiling.** Repeat the common-support and within-cell comparisons between two independent observation products (AGB: ESA-CCI vs GEDI L4B or an FIA-based map; SOC: SoilGrids vs gSSURGO). Their mutual agreement is the ceiling against which model skill is read; without it a low within-cell correlation cannot be attributed to the model rather than to observation noise.
6. **Why only AGB gets a downscaled comparator.** All natural PFTs (and crops, since `create_crop_landunit=.false.`) share one soil column, so coarse SOC cannot be redistributed by PFT fraction. Any within-cell SOC skill therefore comes from running the model at 4 km (soils, climate, and the litter inputs they drive). SOC is the cleanest test of high-resolution *modeling*; AGB measures how much fine land cover alone contributes.

**Interpretation:** Report mean-stock accuracy and within-cell pattern agreement separately. The model may have a systematic carbon-stock bias while correctly locating local highs and lows, or may match coarse means while adding fine detail that does not agree with observations. Interpret AGB and SOC independently.

**Plot:** Two rows (AGB and 0–30 cm SOC) of observation, 0.5° ELM, and 4 km ELM maps with shared units and color scales. Add a compact common-support skill panel and a within-cell anomaly/skill panel. Put extra downscaled maps in the supplement if the main figure becomes crowded.

**Data checks before quantitative claims:** The current poster script labels ESA-CCI bands as 2010 and 2014–2020, but the local processed NetCDF does not store band years; verify the source-year mapping and biomass-to-carbon conversion. The processed ESA-CCI file is already on an approximately 0.04° grid, so document its resampling provenance. SoilGrids is a spatial estimate rather than an annual SOC time series. The poster comparison remains illustrative until time, depth, units, and masks are reconciled. See [plot_biomass_soc_panel.py](../carbon_offset_poster/codes/plot_biomass_soc_panel.py).

### Figure 2 / Results 3.2 — Regional futures and management benefits

**Question:** How do regional forest carbon stocks evolve, and how large are the paired management effects?

**Analysis**

- The plotted stock is TOTECOSYSC (ecosystem + products; see §2). Within a resolution every future case starts from the same 2024 restart, so paired benefits are exactly zero in 2024.
- Establish the historical state and the four Default SSP trajectories. Show a compact historical interval rather than making the entire 1850–2023 spin-up/transient history a main figure.
- Calculate RF − Default and RH − Default within each SSP at both resolutions. Summarize early, middle, and late future windows as well as trajectories.
- Show Default − DF in a distinct panel as an idealized avoided-loss bound. Keep stock differences and NBP fluxes separate.
- Recompute every regional number from the selected cohort; legacy poster and figure values are not manuscript estimates.

**Plot:** Default historical-to-future regional carbon trajectories, paired RF/RH additional-storage trajectories or period summaries, and a clearly labeled DF panel. Use small multiples or a compact SSP summary so that scenario and resolution lines remain readable. Put complete NBP and flux trajectories in the supplement if necessary.

### Figure 3 / Results 3.3 — Spatial heterogeneity hidden by aggregation

**Question:** Where do management gains vary within coarse grid cells, and how much spatial information is lost when results are averaged?

**Analysis**

- Use RF as the primary management example and RH as a consistency check.
- Compare native 4 km RF gain, the same 4 km gain area-weighted to 0.5°, native 0.5° gain, and a land-cover-downscaled coarse comparator where it can be constructed consistently.
- Report area-weighted benefit distributions, high- and low-gain tails, and variation within coarse cells. Relate variation to forest fractions, the management perturbation, soil/water conditions, and disturbance exposure using predefined strata or quantitative relationships.
- Distinguish averaging of one simulation from differences between independently configured simulations. For a downscaled management gain, reconstruct Default and RF fields consistently before taking their difference.

**Plot:** Matched RF-gain maps at native 4 km, aggregated 4 km, and native 0.5°; one or two predefined regional zooms; an area-weighted cumulative distribution or quantile plot; and a compact within-cell heterogeneity statistic. Headline number: the share of area-weighted spatial variance of the RF gain that lies within 0.5° cells, 1 − var(aggregated)/var(native 4 km), i.e. the information removed by aggregation. Also report it with a band around 30.833°N excluded.

### Figure 4 / Results 3.3 — Carbon-pool and process explanations

**Question:** Which pools and fluxes explain management benefits, and what role does SOC actually play?

**Analysis**

- Show two different quantities: existing ecosystem carbon stocks under Default and the **signed changes** in each pool under RF − Default and RH − Default. A large standing SOC pool does not, by itself, establish a large management-induced SOC gain.
- Close TOTVEGC, CWDC, TOTLITC, TOTSOMC **and the derived product pool** against TOTECOSYSC. Omitting the product pool (and vegetation storage/transfer pools) is the likely cause of the legacy several-percent residual. Verify the derived product term is near zero in early transient years.
- **Accounting-boundary test.** Report RF − Default and RH − Default at three boundaries: aboveground vegetation (`TOTVEGC_ABG`), in-situ ecosystem (TOTECOSYSC minus products), and ecosystem + products. Check whether the benefit size, the RF/RH ratio and the Figure 5 selections change with the boundary. RF (zero harvest) and RH act on the product pool directly, so this boundary may matter as much as the aboveground-versus-total distinction.
- **Decompose the RF bundle.** Classify cells before looking at benefits into (a) cells where RF changes land cover (forest restoration) and (b) cells where RF only stops harvest on existing forest (protection). Report area, benefit and pool response for each stratum. This replaces post hoc correlation with forest fraction or soil moisture as the primary spatial mechanism, and quantifies how much of "RF" is restoration versus protection.
- Examine NEP, land-use/product-pool flux, and complete fire loss in the NBP budget. Use the restoration/protection strata to connect regional flux findings to local benefit patterns.
- Interpret a modeled negative SOC response as a model result under the specified scenario and horizon, rather than a general empirical claim about restoration.

**Plot:** A Default stock-pool composition panel (including products); signed RF/RH pool contributions; the three-boundary benefit comparison; and restoration versus protection strata. Keep the NBP process decomposition to one small panel or move it, with detailed pool accounting, to the supplement.

### Figure 5 / Results 3.4 — Consequences for spatial prioritization

**Question:** Given the same physical area budget, does finer spatial information change where management is prioritized?

**Minimum experiment**

1. Choose one paired scenario and period to establish the method, initially RF − Default under SSP3-7.0 for 2091–2100. Define a **common eligible land area** before looking at benefits. If management feasibility is unavailable, call this a modeled land-screening exercise rather than project siting.
2. For every 4 km eligible cell i, calculate its period-mean benefit density: b(i) = mean[C_RF(i,t) − C_Default(i,t)]. Use a density such as Mg C per eligible hectare, not total carbon per grid cell, for ranking.
3. Make a coarse decision map by area-weighted aggregation of those same 4 km benefit densities to 0.5°. Rank eligible land separately using the native 4 km and aggregated 0.5° maps. Select the same physical area, first 20% and 30% of the common eligible domain.
4. Prespecify ties and the last cell at the area cutoff. If only part of a coarse cell is needed, account for its area and expected benefit proportionally; do not use hidden 4 km values to choose particular pixels inside that coarse cell.
5. Compare selected-area overlap, total modeled benefit captured (sum of benefit density × selected area), benefit per selected hectare, and separately reported disturbance exposures.

**Why the scoring reference matters:** The 4 km selection maximizes benefit on the 4 km field used to rank it. Scoring both selections on that same field will favor the 4 km selection by construction. This comparison quantifies model-internal information lost through aggregation. It is not independent evidence that real-world outcomes would improve.

**Extensions after the minimum experiment**

- Plot a selected-area versus captured-benefit curve, keeping 20% and 30% as readable anchors.
- First compare risk exposure of the potential-only selections. Then impose the same clearly defined water-stress or fire-loss screen on both selection approaches and report the carbon-benefit tradeoff. Keep fire and water components visible; repeat without the HDM-affected fire component.
- Carry selection masks from one SSP or time window into another SSP or window and rescore them there. This tests within-model stability rather than observational accuracy.
- Compare the aggregated-4-km primary coarse map with the land-cover-downscaled 0.5° field and native 0.5° simulation. The native cross-resolution comparison includes input and spin-up differences.

**Plot:** A map distinguishing land selected by both approaches, only 4 km, or only the coarse approach; an area-budget versus captured-benefit curve; and a small comparison of selected-area carbon benefit and individual disturbance exposures. Cross-SSP/time overlap can be a supplementary heatmap.

### Main tables

1. **Simulation matrix** from [CASE_MATRIX.md](CASE_MATRIX.md): resolution, SSP, scenario, years, shared and differing inputs, and the effective resolution of each driver (including HDM and the lightning climatology).
2. **Accounting definitions and boundaries:** each stock/flux metric, its equation and pools (TOTECOSYSC includes products), the three Figure 4 boundaries, time windows and interpretation.
3. **Evaluation datasets and metrics:** products, years, native resolution, matching procedure, statistics, and the observation-versus-observation ceiling.

## 4. Results writing sequence

Write one finding per Results subsection and keep interpretation proportional to its evidence:

1. **3.1:** State separately which observed AGB and SOC patterns are reproduced at common support and within coarse cells.
2. **3.2:** Give recomputed regional trajectories and RF/RH benefits across SSPs, with DF clearly identified as idealized.
3. **3.3:** Quantify local distributions and explain the signed vegetation/SOC and process contributions.
4. **3.4:** Give equal-area changes in selected location, benefit, and exposure, followed by cross-scenario and temporal robustness.

Use observed or computed values only after the corresponding comparison has been completed. Greater map detail alone does not establish greater accuracy.

## 5. Discussion structure

### 5.1 When does higher resolution add credible information?

Synthesize Figure 1 with Figures 3 and 5. Discuss what the observational comparison supports for AGB and SOC, which fine patterns a land-cover-downscaled coarse field already reproduces, and where native 4 km modeling adds or fails to add useful information. Regional agreement and local differences answer different questions. Use the AGB/SOC contrast explicitly: AGB skill partly reflects fine land cover (the downscaled comparator), whereas within-cell SOC skill can only come from running at 4 km.

### 5.2 Why do management benefits vary across the landscape?

Explain the influence of forest composition, land-use/harvest change, local conditions, and carbon-pool responses on the Figure 3 patterns. Use Figure 4 to separate existing carbon stocks from management-induced changes. Connect SOC to accounting completeness without inferring a large SOC management benefit from the size of its standing stock. Discuss the product-pool boundary alongside SOC: whether harvested-product carbon is counted can change the RF and RH benefits as much as soil can. Use the restoration/protection split to explain what the RF bundle actually delivers.

### 5.3 How do disturbance and scenario uncertainty affect priorities?

Discuss how modeled fire and water stress relate to gains and selection stability. Report fire's dependence on the coarse HDM input, the sensitivity of risk screens, and differences across SSPs and time windows. The vulnerability indicators do not estimate a project's reversal probability.

### 5.4 What do the equal-area results mean for management?

Explain the locations and benefits affected by coarse aggregation, the mathematical advantage when selection and scoring use the same 4 km field, and what remains stable under alternative scoring periods or scenarios. Position 4 km outputs as information for regional or subregional screening. Operational project selection also requires land eligibility, ownership, costs, and verification information.

The RF:RH:DF magnitudes do not rank three equally implementable policies: DF is an idealized bound, RF a bundle, RH a small perturbation; compare per eligible or treated hectare before any policy comparison. For carbon-credit concepts, keep one short paragraph: additionality is defined only relative to the modeled Default; the risk indicators inform permanence but are not reversal probabilities; leakage is not simulated; and credited quantities must match the pool and product boundary used (Table 2).

### 5.5 Scope and limitations

State the relevant model/input constraints: differing 0.5° and 4 km configurations and separate spin-ups; effective resolution of drivers (HDM bilinear from 0.5°, the same SSP2 HDM for all SSPs, a 1995–2011 lightning climatology, 1.9°×2.5° N deposition); crit_dayl_stress and the 30.833°N discontinuity; a single shared soil column and no forest age structure; instantaneous DF conversion and the bundled RF definition; unrepresented disturbances (insects, windthrow, prescribed burning); observational product uncertainty; a single model; and market feedbacks outside ELM. Separate limitations that affect magnitude from those that could change sign or ranking. Distinguish modeled additional ecosystem storage from creditable offsets.

## 6. Priority work order

1. Freeze the actual case/version mapping, units, masks, periods, and carbon-stock definition.
2. Complete Figure 1's common-support and within-cell evaluations, including the ESA-CCI provenance checks and the second observation product for the ceiling.
3. Recompute Figure 2's paired benefits and Figure 3's spatial distributions from the same cohort.
4. Close Figure 4's carbon-pool accounting (with the derived product pool), the three-boundary test, the restoration/protection split, and the process budget.
5. Run the minimum Figure 5 equal-area experiment, then risk and cross-scenario/time tests.
6. Write Results from the finalized figures; use the Discussion to explain what each tested result permits us to conclude.
