# Analysis framework — high-resolution land modeling of forest carbon management in the southeastern U.S.

*Outline for sharing, 2026-09-29. Summarizes the working plan in
[MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md); where they differ, the
blueprint governs. No results are reported here.*

**Working title:** High-resolution land modeling reveals spatial opportunities
for forest carbon management in the southeastern United States

## 1. Question and contribution

- **Central question:** What does high-resolution land modeling reveal about
  forest carbon management that regional totals conceal, and does that
  information change where management should be prioritized?
- **Contribution:** a within-model test of the value of spatial resolution
  (4 km vs 0.5°) for estimating management benefits and choosing priority
  areas, with observational evaluation of the fine-scale detail.
- **Gap addressed:** regional assessments give broad carbon trajectories but
  not where management yields the largest benefit at acceptable disturbance
  exposure. Similar regional totals can hide very different local patterns.

## 2. Simulations

- **Model:** E3SM Land Model (ELM) with carbon, nitrogen and phosphorus
  cycles, dynamic land use and fire, over the southeastern U.S. at **4 km**
  and **0.5°**. The 4 km grid nests exactly within the 0.5° grid.
- **Period:** spin-up, historical transient 1850–2023, future 2024–2100
  under **four SSPs** (SSP1-1.9, 2-4.5, 3-7.0, 5-8.5).
- **Scenarios**, all starting from the same 2024 state:
  - **Default:** land use and harvest following the SSP.
  - **RF, restoration/protection:** forest restoration plus no harvest on
    existing forest.
  - **RH, reduced harvest:** lower prescribed harvest rates.
  - **DF, idealized deforestation:** forest converted to grassland; used only
    as a bound on avoided loss, not as a policy option.
- **Benefit metrics:** additional carbon storage = RF − Default and
  RH − Default; avoided-loss bound = Default − DF. Each difference is taken
  between runs with identical parameters. The primary stock includes
  vegetation, litter, dead wood, soil and harvested-product carbon.

## 3. Four-step analysis

| Step | Question | Main analysis | Figure |
|---|---|---|---|
| **1. Evaluate** spatial patterns against observations | Is the extra 4 km detail credible, and is it more than fine land cover alone explains? | Compare aboveground biomass and soil carbon (0–30 cm) with observation-based maps at the common 0.5° scale and *within* 0.5° cells | Fig. 1 |
| **2. Quantify** regional trajectories and management benefits | How much carbon does management add, and do the resolutions agree on regional totals? | Regional stock trajectories and RF/RH/DF benefits for four SSPs, at both resolutions, early/mid/late century | Fig. 2 |
| **3. Explain** spatial heterogeneity | What local differences do regional totals hide, and which carbon pools and processes cause them? | Share of spatial variation lost by averaging to 0.5°; carbon-pool contributions; restoration vs protection components of RF | Figs. 3–4 |
| **4. Test** consequences for prioritization | For the same land area, does 4 km information change *where* to manage, and at what risk? | Equal-area selection (20%, 30% of eligible land) using fine vs coarse maps; overlap, captured carbon, disturbance exposure | Fig. 5 |

Each step builds on the previous one: credible detail → size of benefits →
what similar totals hide → whether it changes decisions.

### Step 1 — Observational evaluation
- Observation-based aboveground biomass (ESA CCI Biomass) and soil organic
  carbon (SoilGrids), with a second independent product for each to show how
  closely two observations agree.
- Skill at the common 0.5° scale: bias, RMSE, spatial correlation.
- Skill **within** 0.5° cells: do local highs and lows in the 4 km model match
  those in the observations?
- Biomass is also compared with a **downscaled 0.5°** field (coarse carbon
  density redistributed by fine land cover). This separates the value of
  finer land-cover input from the value of running the model at 4 km. Soil
  carbon has no such shortcut in the model, so it is the cleanest test of 4 km
  modeling.

### Step 2 — Regional benefits
- Default trajectories for the four SSPs; RF and RH benefits per SSP at both
  resolutions; DF shown separately as an idealized bound.
- Stock differences are kept distinct from annual or cumulative fluxes.

### Step 3 — Heterogeneity and mechanisms
- Compare native 4 km, 4 km averaged to 0.5°, and native 0.5° benefit maps.
- Headline number: the fraction of spatial variation in benefits that lies
  inside 0.5° cells, i.e. what coarse maps cannot see.
- Carbon pools: where the added carbon goes (vegetation, soil, litter/dead
  wood, products), and how the answer changes with the accounting boundary
  (aboveground only, ecosystem, ecosystem + products).
- RF split into **restoration** cells (land cover changes) and
  **protection** cells (harvest stops on existing forest).

### Step 4 — Equal-area prioritization
- Select the same area of eligible land by ranking benefit per hectare on
  (a) the 4 km map and (b) the same map averaged to 0.5°.
- Compare location overlap, total carbon captured and benefit per hectare,
  plus a curve of captured carbon versus area selected.
- **Risk screen:** exclude land above fixed thresholds of modeled fire loss,
  water stress or carbon variability, then select again. The coarse map sees
  only averaged risk, so it may keep high-risk patches that the 4 km map
  avoids.
- **Robustness:** select under one scenario or period and evaluate under
  another; repeat with alternative coarse maps and without the fire
  component.

## 4. How resolution is compared

| Comparison | What it isolates |
|---|---|
| 4 km vs 4 km averaged to 0.5° | Information lost by averaging, within the same simulation (primary) |
| 4 km vs downscaled 0.5° | Whether fine land cover alone reproduces the 4 km result |
| 4 km vs native 0.5° run | Full difference between two model configurations |

## 5. Principles and boundaries

- Finer maps are not automatically more accurate; spatial detail is credited
  only where observations support it.
- Modeled benefits already include simulated fire losses, so risk is used to
  **screen** locations, never subtracted a second time.
- Selecting and scoring on the same 4 km field favors 4 km by construction;
  out-of-sample tests show whether an advantage is stable.
- Risk indicators describe modeled exposure, not project reversal
  probability. Results are modeled carbon storage, not issued carbon credits;
  leakage and economics are outside the model.
- Known limits: some drivers are coarser than 4 km (e.g. population density
  and lightning used by the fire model), a single model, and no forest age
  structure.

## 6. Planned outputs

- **Five figures:** (1) observational evaluation; (2) regional benefits;
  (3) heterogeneity hidden by aggregation; (4) carbon-pool and process
  explanation; (5) equal-area prioritization.
- **Three tables:** simulation design and driver resolution; carbon
  accounting definitions and boundaries; evaluation datasets and metrics.
