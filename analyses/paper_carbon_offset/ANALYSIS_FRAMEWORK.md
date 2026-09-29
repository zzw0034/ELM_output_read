# Analysis framework — high-resolution ELM and forest carbon management in the southeastern U.S.

ELM simulations at 4 km and 0.5°, four SSPs, Default vs restoration/protection
(RF) and reduced-harvest (RH) scenarios. Derived from
[MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md), which governs.

| Step | Question | Main analysis | Figure |
|---|---|---|---|
| **1. Evaluate** spatial patterns against observations | Is the extra 4 km detail credible, and is it more than fine land cover alone explains? | Compare aboveground biomass and soil carbon with observation-based maps at the common 0.5° scale and within 0.5° cells | Fig. 1 |
| **2. Quantify** regional trajectories and management benefits | How much carbon does management add, and do the resolutions agree on regional totals? | Regional stock trajectories and RF/RH benefits for four SSPs at both resolutions | Fig. 2 |
| **3. Explain** spatial heterogeneity | What local differences do regional totals hide, and which carbon pools and processes cause them? | Spatial variation lost by averaging to 0.5°; carbon-pool contributions; restoration vs protection components of RF | Figs. 3–4 |
| **4. Test** consequences for prioritization | For the same land area, does 4 km information change where to manage, and at what risk? | Equal-area selection (20%, 30% of eligible land) using fine vs coarse maps | Fig. 5 |

## Step 1 — Evaluate

- Observations: aboveground biomass (ESA CCI Biomass) and 0–30 cm soil organic
  carbon (SoilGrids), plus a second independent product for each as a ceiling
  on achievable skill.
- Skill at the common 0.5° scale: bias, RMSE, spatial correlation.
- Skill within 0.5° cells: do local highs and lows in the 4 km model match the
  observations?
- Downscaled comparator (0.5° carbon density × 4 km land cover) separates the
  value of finer land-cover input from the value of running the model at 4 km.

## Step 2 — Quantify

- Default carbon trajectories for four SSPs.
- Additional storage from RF and RH relative to Default, per SSP, at both
  resolutions, for early, mid and late century.
- Stock differences kept separate from annual and cumulative fluxes.

## Step 3 — Explain

- Compare native 4 km, 4 km averaged to 0.5°, and native 0.5° benefit maps.
- Headline number: share of spatial variation in benefits that lies within
  0.5° cells.
- Carbon pools gaining or losing carbon (vegetation, soil, litter/dead wood,
  products), and how the benefit changes with the accounting boundary.
- RF split into restoration (land-cover change) and protection (harvest
  stopped on existing forest).

## Step 4 — Test

- Rank eligible land by benefit per hectare on the 4 km map and on the same
  map averaged to 0.5°; select equal areas.
- Compare location overlap, carbon captured, benefit per hectare, and a curve
  of carbon captured versus area selected.
- Risk screen: exclude land above fixed thresholds of fire loss, water stress
  or carbon variability, then select again.
- Robustness: select under one scenario or period and evaluate under another.
