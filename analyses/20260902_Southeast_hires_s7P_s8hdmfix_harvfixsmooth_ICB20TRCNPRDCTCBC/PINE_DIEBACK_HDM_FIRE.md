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

### How firmly is fire established? Strongly implicated, not proven

Two results qualify the attribution and should be quoted alongside it.

**Fire is not merely a proxy for warm sandy sites.** Stratifying on temperature
and sand and then splitting each stratum into fire terciles, the death rate
still rises with fire in 7 of 8 strata, sometimes steeply:

| stratum | n | low fire | mid fire | high fire |
|---|---|---|---|---|
| 14-17 C, sand 0-50% | 24083 | 0.0% | 0.7% | 11.5% |
| 17-19 C, sand 50-70% | 5590 | 0.6% | 4.2% | 9.8% |
| 17-19 C, sand 70-101% | 2911 | 9.6% | 17.8% | 12.8% |
| 19-30 C, sand 50-70% | 874 | 0.0% | 3.8% | 61.9% |
| 19-30 C, sand 70-101% | 6485 | 8.3% | 40.0% | 88.7% |

Partial rank correlation of fire with death, controlling for temperature and
sand, is 0.171 - real and independent.

**But temperature is the stronger raw predictor**: rank correlation with death
is 0.590 for temperature against 0.185 for fire and 0.286 for sand. That does
not demote fire, because burned area in this model is itself driven by
temperature and fuel moisture, so temperature plausibly acts largely *through*
fire. It does mean the two pathways cannot be separated from output diagnostics
alone.

**And the same fire did not stop the oak.** Fire is a column-level flux shared
by every PFT in the natural-vegetation column. In the very gridcells where pine
went to zero, broadleaf deciduous temperate tree LAI rose monotonically through
the whole AD phase - 1.78 at year 21, 2.16 at 41, 2.20 at 81, 2.29 at 201 - and
its vegetation carbon went from 1310 to 2663 gC/m2 while the pine beside it
collapsed. So fire alone is not lethal; it is lethal to an evergreen that
carries its leaf fuel year-round and cannot re-leaf from storage each spring
the way a deciduous tree does. That PFT asymmetry is inference from the
behaviour, not something these diagnostics measure directly.

**The decisive test** is a rerun: repeat a small region of the AD spin-up with
the corrected HDM, or with fire disabled, and see whether the pine survives.
Nothing in the existing output can settle it.

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

The reason is that a dead patch has nothing to photosynthesise with. Tracking
the dead cohort's pine pools through both spin-ups:

| stage | LEAFC | CPOOL | DEADSTEMC | TOTVEGC | GPP | NPP |
|---|---|---|---|---|---|---|
| AD 21 | 118.3 | 0 | 271 | 640 | 2.98e-05 | 1.11e-05 |
| AD 41 | 38.7 | 57.1 | 106 | 295 | 9.86e-06 | 3.38e-06 |
| AD 81 | 2.57 | 8.50 | 5.84 | 22.5 | 6.91e-07 | 1.88e-07 |
| AD 201 | 0.137 | 0.729 | 0.119 | 1.18 | 4.16e-08 | 1.00e-08 |
| CNP 1 | 0.148 | 0.894 | 1.34 | 3.11 | 0 | -2.81e-08 |
| CNP 441 | 0.104 | 0.484 | 0.840 | 1.92 | 3.03e-08 | 6.69e-09 |
| healthy pine, CNP 441 | 187.4 | 259.4 | 8900 | 12320 | 4.45e-05 | 1.61e-05 |

GPP scales with leaf area, so at LAI ~0.001 the patch fixes 0.07% of what a
healthy pine fixes. Its NPP is positive but is 0.21 gC/m2/yr; at that rate
reaching the healthy stand's 12320 gC/m2 would take tens of thousands of years.
And it is not even creeping upward: LEAFC *falls* from 0.148 at the start of the
corrected final spin-up to 0.104 after 441 years, so leaf turnover and
respiration consume the tiny gain. This is a stable fixed point at essentially
zero, not slow recovery.

Nothing can bootstrap it. ELM here runs with prescribed PFT areas and no
dynamic vegetation, and there is no establishment or seed flux into an existing
patch that has lost its carbon - the only seed terms come from land-cover-change
transitions that change a patch's area. Growth is funded by photosynthesis from
existing leaves, so once the leaves are gone the patch is in an absorbing state.
Fixing HDM afterwards restores fire suppression but gives the pine nothing to
grow back from.

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
