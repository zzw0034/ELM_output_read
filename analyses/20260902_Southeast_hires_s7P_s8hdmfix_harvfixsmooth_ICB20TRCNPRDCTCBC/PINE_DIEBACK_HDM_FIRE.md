# Pine dieback in the SEUS 4 km spin-up: cause, extent, and what it costs

Found 2026-09-09 while asking why parts of Georgia and Florida look pale on the
GPP maps in this analysis. Recorded here because every 4 km SEUS run in this
lineage inherits it, including the future scenarios.

## What is wrong

On 9.1% of pine patches (5580 of 62924) the needleleaf evergreen temperate tree
PFT is at **exactly zero leaf carbon**, permanently. Not a thinned canopy, a
dead one: LEAFC 6e-5 gC/m2 and GPP 2e-9 gC/m2/s.

Those patches carry 44-45% of the natural-vegetation area of the gridcells they
sit in, so the gridcell means collapse with them. Every other PFT in the same
gridcells is healthy or slightly better than its neighbours:

| per-PFT, area-weighted, 2010 | GA affected | GA control | FL affected | FL control |
|---|---|---|---|---|
| pine LAI | 0.45 | 2.08 | 0.03 | 1.82 |
| pine LEAFC gC/m2 | 42.0 | 195.7 | 2.6 | 171.7 |
| broadleaf deciduous LAI | 2.98 | 2.76 | 2.62 | 2.31 |
| C3 grass LAI | 6.17 | 6.00 | 6.91 | 5.69 |

Restoring pine alone closes 88% of the gridcell GPP gap; pine plus the
broadleaf evergreen shrub, which fails the same way on 1.7% of the area,
closes all of it.

## Why it happened

**Fire during the accelerated-decomposition spin-up, which ran with human
population density identically zero.**

The dying cohort was not starving. At their year-21 pre-mortem state their
carbon balance is only mildly worse than the survivors' (GPP 0.83 of it, NPP
0.77, MR/GPP 0.515 vs 0.474) and **NPP is positive for 100% of them**. What
separates them is `COL_FIRE_CLOSS`, 2.95x higher: 13.1% of their standing
vegetation carbon burned per year against 2.8% for survivors, rising to 20.3%
by year 41. A stand establishing from bare ground cannot outgrow that.

The dose-response, binning every pine patch alive at AD year 21 by its fire
loss that year and asking how many are dead by year 201:

| fire quintile | mean COL_FIRE_CLOSS gC/m2/s | died |
|---|---|---|
| 1 | 4.8e-08 | 0.1% |
| 2 | 4.9e-07 | 0.4% |
| 3 | 1.1e-06 | 2.8% |
| 4 | 1.7e-06 | 6.2% |
| 5 | 2.8e-06 | 31.0% |

`HDM` is exactly 0 over the whole domain for all 201 years of the AD spin-up.
Lightning is on and near-uniform (`LNFM` 0.00226 vs 0.00224 between the two
cohorts), so ignition supply is not what differs. In ELM's fire
parameterization population density drives both human ignition and fire
*suppression*; at zero there is no suppression.

The root cause is documented in the user's own note,
`ELM_makeSurfdata/Make_surface_data/s8_update_hdm/HDM_high_resolution_cpl_bypass_fix_20260717.md`:
the CPL_BYPASS HDM reader had the file dimensions **hardcoded to 720 x 360**,
while the SEUS file is 504 x 324. `nf90_get_var` failed on the shape mismatch,
**the return code was written to `ierr` and never checked**, and the
zero-initialized arrays flowed straight into the fire calculation. The model ran
201 years without complaint.

The timeline: the AD spin-up ran 2026-07-12/13, before the patch. The `hdmfix`
final spin-up started 2026-07-17, after it, and does read HDM correctly (mean
5.128, max 39.53) with fire an order of magnitude lower. **The fix arrived one
stage too late.**

## Why it never recovered

The collapse is one-way. Across 38 consecutive spin-up and transient outputs
spanning about 800 model years and 63000 patches, there are 26 transitions from
dead (LAI < 0.5) back to healthy (LAI > 1.5). The dead fraction is 1.0% at AD
year 21, 6.6% at 41, 8.9% at 81, and then locked at 9.0-9.1% through 441 years
of corrected final spin-up and all 174 transient years. 97% of the deaths happen
in the first 80 years of the AD phase, 63% of them between years 21 and 41.

## How much it costs

Counterfactual: give each dead pine patch the mean carbon of surviving pine in
the same temperature band, at its own PFT weight.

| | GPP bias | vegetation C bias | affected cells |
|---|---|---|---|
| whole SEUS domain | 2.1% low | 2.4% low | 7.2% |
| Georgia box | 3.1% low | 3.9% low | 8.7% |
| **Florida box** | **11.3% low** | **16.8% low** | **38.2%** |
| affected cells themselves | 28% low | 39% low | - |

Domain totals: GPP 2.6131 PgC/yr against a counterfactual 2.6701, vegetation
carbon 11.65 PgC against 11.95.

## If it is not fixed

Defensible for:

- **Domain-total carbon budgets.** A 2% bias is below the spread of other
  structural choices in the run.
- **Scenario differences.** The management scenarios all branch from the same
  restart, so an identical hole sits in every one of them and largely cancels in
  the differences. Report deltas, not absolutes.
- **Anything north or west of the affected zone.** The hole is confined to the
  warm sandy coastal plain.

Not defensible for:

- **Anything reported for Florida separately.** 38% of Florida's land cells are
  affected and its biomass is 17% low. Real Florida flatwoods are pine
  dominated; the run says they are not.
- **Biomass validation against observations.** A comparison against ESACCI or
  similar will show a Florida-shaped bias that is a model initialization
  artifact, not a model-physics result.
- **Management scenarios evaluated in absolute terms in the affected zone.** A
  patch with no pine cannot respond to reduced harvest or reforestation, so the
  scenario response there is suppressed for the wrong reason.

Minimum action if not rerunning: mask or flag the affected cells in any map or
regional total, and state the limitation. The affected set is reproducible from
the h1 output as pine patches with annual mean TLAI < 0.5.

## If it is fixed

The rerun must start at the **AD spin-up**, not the final spin-up, which already
inherits the damage. That is roughly 201 + 441 + 174 = 816 model years, against
the 174-year transient's measured 66 hours on 12 nodes, so on the order of two
weeks of wall time, plus redoing every downstream scenario.

Cheap sanity check for any future SEUS spin-up: look at pine LAI in the h1
output around AD years 20-80. The whole outcome is decided in that window.

## Reproducing

All of it comes from the `h1` PFT-vector history files (`hist_dov2xy = .false.`),
which exist for both spin-ups and the transient. A 50-variable screen of
gridcell-mean h0 fields found nothing; one h1 read made the cause obvious. When
a gridcell-average field looks inexplicably low, go to h1 first.

Watch two traps. The AD year-0001 h1 file is the cold start with LAI 0
everywhere, so it must be excluded from any "first year dead" test. And
`PCT_CROP` and `PCT_NATVEG` in the landuse timeseries file are static 2-D
fields, not time-varying, so indexing them by a time step silently broadcasts a
single latitude row.
