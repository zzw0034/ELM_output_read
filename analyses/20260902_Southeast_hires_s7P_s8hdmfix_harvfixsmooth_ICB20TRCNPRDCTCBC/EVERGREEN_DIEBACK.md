# Evergreen PFTs stranded at near-zero leaf area in the SEUS spin-ups

Investigation record, 2026-09-09 to 2026-09-10. Started from a colour artifact
on this run's GPP maps and ended in a structural property of ELM's phenology.

Companion files: [ASK_COLLEAGUES.md](ASK_COLLEAGUES.md) is the short version to
send out. [README.md](README.md) covers the every-20-years QC maps this
directory was originally built for.

Everything below is measured from model output or read out of the E3SM source.
Inference is labelled as such. Section 8 lists what was claimed and then
retracted, because several plausible explanations died on contact with data and
knowing which ones matters for trusting the rest.

## The story in six sentences

The evergreen PFTs sit at near-zero leaf carbon on 9% of their patches at 4 km
and 78% at 0.5 degrees, permanently, while every deciduous PFT beside them is
healthy. The reason it is permanent and PFT-specific is structural:
`CNEvergreenPhenology` sets `bgtr = 0` and has no onset event, so an evergreen's
leaves come only from current allocation, which photosynthesis funds, which needs
leaves - while the deciduous subroutines re-flush from storage every spring. What
pushed patches into that trap differs by resolution and both causes were our own
configuration: at 4 km, fire, because a hardcoded 720x360 dimension made the HDM
reader fail silently and take the fire model's suppression term to zero; at 0.5
degrees, nitrogen starvation, because the case labelled `ad_spinup` was built
without `-bgc_spinup on` and never ran accelerated decomposition. A controlled
rerun proved the 4 km diagnosis: fixing only the HDM reader cut the stranded
fraction from 8.9% to 0.9%, helping the two evergreen PFTs and leaving all five
deciduous ones untouched to the decimal. Both causes are now fixed, so the chains
can be rebuilt - section 10 is the plan.

## Where to look for what

| you want | section |
|---|---|
| what the symptom looks like, with numbers | 1 |
| the mechanism, from source | 2 |
| why 4 km and 0.5 degrees failed for different reasons | 3 |
| why the 0.5 degree chain is worse than the dieback alone | 4 |
| the controlled experiment that proved the 4 km diagnosis | 5 |
| why every timing statement here has a resolution limit | 6 |
| what is still unexplained | 7 |
| explanations advanced and then abandoned | 8 |
| the cost of doing nothing | 9 |
| **the rerun plan** | **10** |
| how to reproduce any of it, and the traps | 11 |

---

## 1. What is wrong

The needleleaf evergreen temperate PFT ("pine") sits at near-zero leaf carbon on
a fraction of its patches, permanently, from early in the spin-up onward.
Broadleaf evergreen shrub does the same. Every deciduous PFT in the same
gridcells is healthy.

| | 4 km chain | 0.5 degree chain |
|---|---|---|
| pine patches stranded | **9.1%** | **78.1%** |
| broadleaf evergreen shrub | collapsed | 100% |
| every deciduous PFT | unaffected | unaffected |

Three properties make it distinctive.

**Binary, not graded.** At 4 km AD year 201: 9.0% of pine patches below LAI
0.01, 90.9% above 1.0, 0.5% in between. At 0.5 degrees: 77.9% below 0.01, the
rest healthy, nothing between, median exactly 0.000 - while not one oak patch is
below LAI 0.5.

**One-way.** 26 transitions from stranded (LAI < 0.5) back to healthy
(LAI > 1.5) across 38 consecutive history outputs spanning ~800 model years and
63,000 patches.

**Set early, then frozen.** At 4 km the stranded fraction is 1.0% at AD year 21,
6.6% at 41, 8.9% at 81, then locked at 9.0-9.1% through 441 years of final
spin-up and all 174 transient years. 97% of the losses happen in the first 80
years of AD; 63% between years 21 and 41.

**Exactly the evergreen PFTs.** Of the seven PFTs present in this domain, the
two with `evergreen = 1` in `clm_params.nc` are affected and the five with
`season_decid` or `stress_decid` are not. No exceptions.

| PFT | evergreen | season_decid | stress_decid | outcome |
|---|---|---|---|---|
| needleleaf evergreen temperate | **1** | 0 | 0 | stranded |
| broadleaf evergreen shrub | **1** | 0 | 0 | stranded |
| broadleaf deciduous temperate tree | 0 | 1 | 0 | fine |
| broadleaf deciduous temperate shrub | 0 | 0 | 1 | fine |
| C3 grass, C4 grass, crop | 0 | 0 | 1 | fine |

## 2. The structural reason: no re-flush pathway for evergreens

`CNEvergreenPhenology` in `components/elm/src/biogeochem/PhenologyMod.F90` sets
a background leaf litterfall rate, `lgsf = 0`, and **`bgtr = 0`** - the
background transfer growth rate - and nothing else. There is no onset event. An
evergreen's leaves come only from current allocation, which photosynthesis
funds, which requires leaves.

`CNSeasonDecidPhenology` and `CNStressDecidPhenology` are several hundred lines
of onset/offset logic that flush `leafc_storage` into `leafc` each growing
season. That is an injection independent of current leaf area, and it is why a
deciduous patch that loses its canopy always gets it back.

This explains the PFT selectivity, the binary distribution and the one-way
behaviour. It does not by itself explain what pushes a given patch over, nor
exactly what holds a stranded patch where it sits - see sections 3 and 6.

## 3. The triggers differ by resolution, and both are our own configuration

### 4 km: fire, from an HDM reader that failed silently

The AD spin-up ran with human population density identically zero for all 201
years. The CPL_BYPASS HDM reader had its dimensions hardcoded to 720 x 360; the
custom SEUS file is 504 x 324; `nf90_get_var` failed on the shape mismatch and
**the return code was written to `ierr` and never checked**, so zero-initialized
arrays flowed into the fire calculation. Documented at
`ELM_makeSurfdata/Make_surface_data/s8_update_hdm/HDM_high_resolution_cpl_bypass_fix_20260717.md`;
the patch landed 2026-07-17, four days after this AD spin-up ran.

In ELM's fire parameterization population density drives both human ignition and
suppression, so at zero there is no suppression. The AD phase amplifies fire
twice more, in `FireMod.F90`:

```fortran
line 586:  if (spinup_state == 1) fuelc(c) = fuelc(c) + ((spinup_mortality_factor - 1)*deadstemc_col(c))
line 983:  if (spinup_state == 1) m_veg = spinup_mortality_factor
```

Fuel load inflated by nine times dead stem carbon, fire-induced vegetation
mortality multiplied by ten. Three amplifications at once, giving ~1e-6
gC/m2/s fire loss against ~1e-8 at 0.5 degrees.

Supporting evidence at 4 km: `COL_FIRE_CLOSS` is 2.95x higher in the dying
cohort pre-mortem, 13.1% of their standing vegetation carbon burned per year
against 2.8% for survivors, and death rate rises 0.1% / 0.4% / 2.8% / 6.2% /
31.0% across fire quintiles. It survives stratification - within temperature and
sand strata the gradient holds in 7 of 8 strata, partial rank correlation 0.171.

**This is now demonstrated, not inferred** - see section 5.

### 0.5 degrees: nitrogen limitation, from an AD spin-up that was never AD

`20260831_seus_halfdeg_ad_spinup` has `spinup_state = 0` and no
`-bgc_spinup on` in `ELM_BLDNML_OPTS`. It ran with normal decomposition despite
the name. Consequence at year 21:

| run | FPG | FPI | SMINN | TOTSOMC | HR |
|---|---|---|---|---|---|
| 4 km AD | **1.000** | **1.000** | 0.090 | 459 | 9.4e-06 |
| 0.5 deg | **0.678** | 0.406 | 0.021 | 118 | 1.5e-06 |

With acceleration on, 4 km has no nitrogen downregulation whatsoever because AD
floods the system with mineral N. Without it, growth is downregulated by a third
with four times less mineral N. Establishment is slow enough that evergreens
never cross the threshold while deciduous flush from storage regardless.

Fire there was two to three orders of magnitude lower than 4 km, and it still
lost eight times as much pine. **Less fire, far more loss** - which is why fire
cannot be the general cause.

**How it was missed.** A search of prior session transcripts finds
`-bgc_spinup on` in exactly one place, a July 2026 script for the 4 km chain, as
`./xmlchange --append ELM_BLDNML_OPTS="-bgc_spinup on"`. It appears in neither
session that built the 0.5 degree cases. Nothing complains when it is absent:
the case builds, runs 201 years, and writes files named `ad_spinup`.

## 4. The 0.5 degree chain has a larger problem than the dieback

Skipping AD also skipped the pool rescaling at the handoff. In
`components/elm/src/data_types/ColumnDataType.F90` around line 3056:

```fortran
if (exit_spinup) then
   m = decomp_cascade_con%spinup_factor(k)
   if (decomp_cascade_con%spinup_factor(k) > 1) m = m / cnstate_vars%scalaravg_col(c,j)
```

`exit_spinup` fires when a `spinup_state = 0` run reads a `spinup_state = 1`
restart. The 0.5 degree restart said 0, so it never fired:

| chain | TOTSOMC at end of "AD" | at start of final spin-up | ratio |
|---|---|---|---|
| 4 km | 697 | 15320 | **22x** |
| 0.5 deg | 2060 | 2173 | 1.05x |

AD pools are *supposed* to be small - accelerated turnover means a smaller
steady-state stock - and the scheme depends on that multiplication. The tell is
that the 0.5 degree "AD" ended with **more** soil carbon than the real one,
which looks healthier and is exactly backwards.

Convergence at the end of each final spin-up:

| | end TOTSOMC | end drift | verdict |
|---|---|---|---|
| 4 km | 16960 | **0.8% / century** | converged |
| 0.5 deg | 6752 | **13.0% / century** | far from equilibrium |

So the whole 0.5 degree carbon state is wrong, not just its evergreens, and the
transient plus seven future scenarios all inherit it.

## 5. Experiment: job 522373

`20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup` is a
clone of the original 4 km AD spin-up, identical in every input, PE layout and
namelist, differing only in an E3SM source that reads HDM correctly. 80 model
years, 12 nodes on the `hpcl-cli185` partition and QoS. It reproduces the
reference configuration of `20260519_Southeast_hires_ICB1850CNRDCTCBC_ad_spinup`
(fire on, no `use_nofire`, HDM actually read), so it is a direct test.

| year | HDM ctrl/expt | fire loss ctrl/expt | **stranded ctrl/expt** | Ndep ctrl/expt |
|---|---|---|---|---|
| 21 | 0.000 / **5.128** | 1.17e-06 / 3.43e-07 | 1.0% / 0.4% | 1.99e-08 / 1.98e-08 |
| 41 | 0.000 / **5.128** | 1.02e-06 / 3.52e-07 | 6.6% / 0.9% | 1.99e-08 / 1.98e-08 |
| 61 | 0.000 / **5.128** | 1.52e-06 / 5.42e-07 | 7.8% / 0.9% | 1.99e-08 / 1.98e-08 |
| **81** | 0.000 / **5.128** | 1.33e-06 / 5.34e-07 | **8.9% / 0.9%** | 1.99e-08 / 1.98e-08 |

**Complete. Job finished 2026-09-10, 12h50m, all four checkpoints.**

The control climbs 1.0 to 8.9% while the experiment is flat at 0.9% from year 41
onward, three checkpoints running. That matters because the control's 8.9% at
year 81 is essentially its final value - it locks at 9.0-9.1% and does not move
through 441 years of final spin-up and 174 transient years.

Of the 6104 patches the control has stranded by year 81, **90.4% are alive in
the experiment**, at mean LAI 1.545 against 1.957 for pine that never came
close. The experiment's own 598 losses are almost entirely a subset of the
control's: 583 of them, so only 15 patches are stranded that the control did not
also lose.

**It helps exactly the evergreens and nothing else**, which is what the
mechanism predicts:

| PFT | ctrl LAI | expt LAI | ctrl stranded | expt stranded |
|---|---|---|---|---|
| needleleaf evergreen temperate | 1.623 | 1.940 | **8.9%** | **0.9%** |
| broadleaf evergreen shrub | 0.496 | 1.080 | **63.2%** | **22.6%** |
| broadleaf deciduous temperate tree | 2.544 | 2.757 | 0.3% | 0.3% |
| broadleaf deciduous temperate shrub | 8.398 | 9.134 | 0.7% | 0.7% |
| C3 grass | 5.372 | 5.694 | 0.3% | 0.3% |
| C4 grass | 5.666 | 7.079 | 0.0% | 0.0% |

The domain state is healthy, not merely different. Fire falls to 40% of the
control and everything else moves modestly upward in the expected direction:
TOTSOMC +15%, TOTVEGC +9%, GPP +7%, NPP +9%, TLAI +10%, SMINN +16%, FPG 0.949 to
0.969. Nothing looks broken; it is simply a less-burned system.

`NDEP_TO_SMINN` matches to three digits throughout, so the Ndep calendar-year
fix that also landed between the two source versions is a no-op here and the
experiment isolates HDM cleanly.

### Conclusion

**Fixing the HDM reader alone is sufficient at 4 km.** It cuts the permanent
pine loss from 8.9% to 0.9% and the evergreen shrub loss from 63.2% to 22.6%,
with no other configuration change - no `use_nofire`, no restart surgery, no
departure from the reference configuration of
`20260519_Southeast_hires_ICB1850CNRDCTCBC_ad_spinup`. A rerun of the 4 km chain
on the current source will largely work.

Two things it does not do. A residual remains, dissected below. And it does not
remove the phenology trap of section 2 - it removes a trigger strong enough to
push patches into it. Any future cold-start spin-up with a different disturbance
regime can strand evergreens again.

### The residual 0.9% is two different things, and one is a separate bug

The 598 pine patches still stranded in the experiment split cleanly:

| | n | mean annual T | FSDS | location |
|---|---|---|---|---|
| A | **193** | **49.85 C** | **0.00** | scattered, 25.5-37.5 N |
| B | 405 | 22.82 C | 176.07 | south Florida, 25.2-30.1 N |

**Group A is not a dieback at all - those gridcells are driven by ocean sentinel
values.** Reading the raw cpl_bypass forcing at their locations gives a constant
`TBOT` of 122.851 C and a constant `FSDS` of **-1111.027 W/m2** for all 44 years,
against 13.8 C and 167.8 W/m2 at a normal inland point. Nothing can grow with a
missing-data flag for sunlight.

This affects **194 land cells, 0.26% of the domain, identically in every 4 km run
we have** - AD control, AD experiment, final spin-up, and the 2010 transient all
show the same 194 cells with `GPP = 0`. They are coastal: Miami, Fort
Lauderdale, Charlotte Harbor, Galveston Bay, the Louisiana coast.

The mechanism is the coastal nearest-neighbour trap in section 10 of
`elm_setup_and_run_guide.md`, but that section says it can never fire at native
resolution. It does here: the 4 km model grid is offset **half a cell** from the
4 km forcing grid, so every cell takes a nearest neighbour and a coastal one can
land on a point flagged as ocean. That claim in the guide has been corrected.

**Fixed 2026-09-10.** The CPL_BYPASS reader picks the nearest `zone_mappings.txt`
row and reads that record without checking it holds data, and 107,661 of the
225,625 rows point at ocean sentinels. Those rows were deleted from all five
mapping tables the 4 km chain uses - `cpl_bypass_full` and the four
`future_clim/ssp*`. Only the broken cells change: a cell whose nearest point was
already valid keeps it, because only farther-or-equal candidates were removed.
Verified by replaying ELM's own nearest-neighbour search over all 75,920 land
cells - 193 changed, 75,727 identical, **zero left on a sentinel**. Originals are
preserved as `zone_mappings.txt.orig_before_sentinel_fix_20260910`, and the full
record with the procedure and how to revert sits in the forcing directory as
`ZONE_MAPPINGS_SENTINEL_FIX_20260910.md`. Script: `fix_zone_mappings.py`, in
this directory and in the forcing directory.

**Group B is the genuine residual**, 405 patches at the hot southern end of
Florida with normal forcing. Below 26 N, 42.4% of pine patches are still
stranded even with the fix - that is the trap still catching the most marginal
sites, consistent with fire remaining amplified in AD by the fuel and mortality
factors even once suppression works.

So the real residual dieback is **0.6%, not 0.9%**, and it is concentrated in
south Florida rather than spread across the domain.

## 6. A limit on every timing statement above

The spin-ups write `hist_nhtfrq = -175200, hist_mfilt = 1`: **one 20-year mean
per file**, ten files for 200 years. The file stamped `0021` is not a year-21
snapshot, it is the mean over years 1-20.

Two consequences, and they were not carried into the timing claims carefully
enough at first.

**Collapse times are smeared and biased late.** Everything above phrased as "the
stranded fraction at year 41" is really "the fraction whose *20-year mean* TLAI
over years 21-40 fell below 0.5". A patch that collapsed in year 2 shows a low
mean immediately; one that collapsed in year 18 still carries most of its peak
in that window and may not be flagged at all. So the distribution of first-flagged
windows is not the distribution of collapse times.

**"They establish first and then fail" is weaker than stated.** It rests on the
dying cohort's years-1-20 mean LAI being 1.126 against 1.581 for survivors. A
mean of 1.126 is equally consistent with a steady 1.126 and with growing to 2.2
by year 10 then collapsing to 0 by year 20. These cannot be distinguished at
this output frequency.

**What is not affected**: the end state (9.1% stranded), the PFT selectivity, the
one-way behaviour over ~800 years, the source-level phenology mechanism, and the
experiment of section 5 - control and experiment were measured identically, so
the comparison holds.

Ten points is also too coarse to judge AD convergence: it cannot distinguish
monotonic approach from oscillation on a sub-20-year scale. The final spin-up is
better at 23 points over 441 years, but has the same blind spot below 20 years.

**Diagnostic run 522626 addresses this.**
`20260910_ADdiag_annual_ICB1850CNRDCTCBC_ad_spinup` is a `--keepexe` clone of the
original AD spin-up - so the *unfixed* HDM reader, where the collapse actually
happens - running 30 years with `hist_nhtfrq = -8760, hist_mfilt = 30`, annual
output, on 20 nodes of `parallel`. It also adds `LEAFN`, `FROOTN`, `LIVESTEMN`,
`LIVECROOTN`, `XSMRPOOL`, `LEAFC_ALLOC`, `LEAFC_LOSS` and `LEAFC_TO_LITTER` to
both tapes, which is what the open question below needs.

## 7. What is still open

**Why a stranded patch sits at break-even instead of recovering or collapsing.**
It is not dead: LEAFC 0.092 gC/m2 with a *positive* NPP of 0.187 gC/m2/yr,
decaying with a time constant of order a thousand years.

The arithmetic is unambiguous. Holding a canopy costs `leafc / leaf_long`
= 0.667 x leafc per year, identical for both states, so

```
leaf allocation needed to hold steady = 0.667 / (NPP per unit leaf carbon)
```

| | stranded | healthy |
|---|---|---|
| GPP per unit leafC, /yr | **9.234** | 7.489 |
| NPP/GPP | **0.221** | 0.362 |
| NPP per unit leafC, /yr | **2.04** | **2.71** |
| leaf allocation needed | **32.7% of NPP** | 24.6% |

So the entire difference reduces to NPP per unit leaf carbon, and the deficit is
**on the respiration side, not photosynthesis** - a sparse canopy is *more*
efficient per unit leaf because it has no self-shading.

What is not explained: MR per unit leaf carbon is 4.89/yr for stranded against
3.56/yr for healthy, 37% higher, **even though its respiring tissue per unit
leaf is lower** - live stem 0.037 against 0.141, live coarse root 0.011 against
0.042, fine root only 11% higher. Tissue inventory does not account for it.
Note also that `AR` exceeds `MR + GR` in both states (by 0.19 x GPP stranded,
0.055 x GPP healthy), pointing at the `xsmrpool` machinery.

And a second inconsistency: fixed allometry with the healthy state's 24.6%
allocation would give a decay rate of -0.165/yr, a six-year collapse. The
observed decay is ~1250 years, 200x slower. Something regulates these patches
close to break-even and it is not a simple fixed-fraction mismatch.

**Being settled now.** Job **522626** is running exactly that: 30 years of the
original AD spin-up at annual resolution with those variables on both tapes (see
section 6). It will decompose maintenance respiration by tissue nitrogen, resolve
the `AR > MR + GR` gap through `XSMRPOOL`, and read the *actual* leaf allocation
fraction from `LEAFC_ALLOC` against `LEAFC_LOSS` and `LEAFC_TO_LITTER` instead of
inferring it from a steady-state assumption. That inference is precisely where
the 200x error came from.

**Whether this is known.** Three questions are out to colleagues in
[ASK_COLLEAGUES.md](ASK_COLLEAGUES.md): has anyone seen it, is the phenology
reading right, and is there a recommended guard.

**Preventive measures identified so far**, cheapest first: initialize AD from an
existing spun-up restart rather than bare ground; keep the establishment phase
benign (here, working fire suppression); **QC per-PFT LAI after every spin-up**,
which is two lines on h1 output and would have caught this immediately at both
resolutions; repair the restart for an otherwise-good chain by setting
`leafc`/`leafc_storage` with matching N and P; a leaf carbon floor in the model,
which is a code change belonging upstream.

There is no viability guard in the code today - a search of `biogeochem/` and
`main/` finds no minimum leaf carbon, and the only seed flux,
`dwt_seedc_to_leaf`, fires only when a patch's *area* changes through a land-use
transition. That is why the 0.5 degree transient partly recovered (78.1% to 9.9%
stranded by 2023) and the 4 km one did not.

## 8. Claims made and then retracted

Six explanations were advanced during this investigation and abandoned. Listing
them because two of them failed the same way.

1. **Carbon starvation / respiration squeeze killed the pine.** Rejected: NPP is
   positive for 100% of the dying cohort before it dies, and among surviving
   pine per-patch MR/GPP flattens at 0.395-0.398 above 20 C, exactly where
   60-70% of patches are lost. The supporting statistic was mean(AR)/mean(GPP)
   over a population including dead patches.
2. **Fire is the root cause.** Demoted: the 0.5 degree chain has two to three
   orders of magnitude less fire and eight times more loss. Fire is a trigger,
   at 4 km, now demonstrated (section 5).
3. **`spinup_mortality_factor` is irrelevant because it only touches dead
   structural pools in `GapMortalityMod`.** Wrong: it also multiplies fire
   vegetation mortality and inflates fuel load in `FireMod.F90`. Only
   `GapMortalityMod` had been checked.
4. **The 0.5 degree run is not a clean control, it is merely establishing
   slowly.** Wrong: its LAI distribution is bimodal, 77.9% below 0.01 and the
   rest healthy. The mean of 0.201 described a state no patch was in.
5. **Stranded patches carry more non-photosynthetic tissue.** Wrong: they carry
   less live stem and less live coarse root per unit leaf.
6. **Fixed allometry means leaf allocation cannot rise to what is needed.**
   Inconsistent with the observed decay rate, which is 200x slower than that
   would predict.

Items 1 and 4 are the same error: **taking a mean over a bimodal population**.
Item 3 is stopping the source search at the first plausible module.

## 9. Impact, if nothing is changed

Counterfactual: give each stranded patch the mean carbon of healthy pine in the
same temperature band, at its own PFT weight.

| | GPP bias | vegetation C bias | affected cells |
|---|---|---|---|
| whole SEUS domain | 2.1% low | 2.4% low | 7.2% |
| Georgia box | 3.1% low | 3.9% low | 8.7% |
| **Florida box** | **11.3% low** | **16.8% low** | **38.2%** |
| affected cells themselves | 28% low | 39% low | - |

Defensible without a fix: domain-total carbon budgets, where 2% is below other
structural uncertainties; scenario *differences*, since every scenario branches
from the same restart and the hole largely cancels; anything outside the warm
sandy coastal plain.

Not defensible: anything reported for Florida separately, where 38% of land
cells are affected and real flatwoods are pine-dominated; biomass validation
against observations, which will show a Florida-shaped bias that is an
initialization artifact; management scenarios evaluated in absolute terms inside
the affected zone, since a patch with no pine cannot respond to reduced harvest
or reforestation.

Minimum action without rerunning: mask or flag the affected cells in any map or
regional total and state the limitation. They are reproducible from h1 output as
pine patches with annual mean TLAI < 0.5.

## 10. Rerun plan

Both root causes are fixed and verified, so the chains can be rebuilt. Nothing
below needs a code change or a new input dataset.

### Prerequisites, both already in place

| fix | where | status |
|---|---|---|
| HDM reader reads any grid and any calendar | `lnd_import_export.F90`, patched 2026-07-17 | in the current `SRCROOT` |
| `zone_mappings.txt` free of ocean sentinels | 5 tables under `Daymet_ERA5_TESSFA2/cpl_bypass_full` | done 2026-09-10, verified |
| `-bgc_spinup on` for any AD case | `ELM_BLDNML_OPTS` | must be set per case, see below |

Proof the first two suffice at 4 km: section 5. Fixing HDM alone cuts the
stranded fraction from 8.9% to 0.9%, and of that residual a third was the
sentinel cells now also fixed.

### Order: 0.5 degrees first

It is the more broken chain and by far the cheaper one. Its `NTASKS_LND` is 571
against 4 km's 2560, on a domain with roughly two orders of magnitude fewer
gridcells, so the whole chain is hours rather than the better part of a week.

### Chain A - 0.5 degrees, rebuild entirely

The existing chain is not salvageable: `20260831_seus_halfdeg_ad_spinup` ran with
`spinup_state = 0`, so `exit_spinup` never fired at the handoff and the final
spin-up started from soil carbon roughly seven times too low. It ended at
6752 gC/m2 still drifting 13.0% per century, against 4 km's 16960 at 0.8%. That
is a broken carbon state, not just missing evergreens, and the transient plus
seven future scenarios all inherit it.

1. **AD spin-up, 200 years, cold start.** The one thing that was missing:
   `./xmlchange --append ELM_BLDNML_OPTS="-bgc_spinup on"`.
   **Gate:** `spinup_state = 1` in `CaseDocs/lnd_in` before submitting. This is
   the entire cause of the chain's problem and it is one line.
2. **Final spin-up, from the AD restart.** **Gate:** `TOTSOMC` must jump sharply
   at the handoff - 4 km went 697 to 15320, a factor of 22. A ratio near 1 means
   `exit_spinup` did not fire and the AD stage was not AD. Then run to
   convergence and require end drift below about 1% per century.
3. **Transient 1850-2023**, then **the seven future scenarios**.

### Chain B - 4 km, rebuild from the AD stage

The final spin-up and everything downstream inherit the stranded evergreens, so
the rerun has to start at AD. Do not restart from any existing 4 km restart file.

1. **AD spin-up, 200 years, cold start**, on the current source. Configuration is
   otherwise the reference one - fire on, no `use_nofire`, `spinup_state = 1`,
   `spinup_mortality_factor = 10` and `nyears_ad_carbon_only = 25` at their
   defaults. Measured cost for the original: 2h40m per 20 years on 12 nodes,
   26.7 h for 200 years; faster on 20.
   **Gates**, all checkable in the first history file:
   - `HDM` mean is about 5.1, not 0
   - zero land cells with annual-mean `FSDS < 1`
   - stranded pine fraction about 0.4%, not 1.0%
2. **Final spin-up.** **Gate:** the same `TOTSOMC` handoff jump as above, then
   end drift below about 1% per century.
3. **Transient 1850-2023.** Measured cost: 66.4 h on 12 nodes for 174 years.
4. **Future scenarios**, which pick up the fixed `future_clim/ssp*` tables
   automatically.

### Expected outcome

Stranded evergreen patches should fall from 9.1% to roughly 0.6%, all of it in
the hot southern end of Florida, and the 194 zero-carbon coastal cells should
disappear entirely. Florida's biomass bias of 16.8% should largely close.

### What the rerun does not fix

The phenology trap of section 2 is untouched. Removing the triggers keeps
patches out of it under *these* conditions; a different disturbance regime can
strand evergreens again. The residual 0.6% is that trap still catching the most
marginal sites.

### Standing checks for any future spin-up

Cheap, and each maps to something that actually went wrong here.

| check | catches |
|---|---|
| per-PFT LAI from the `h1` tape after spin-up | the entire dieback, which a 50-variable gridcell-mean screen missed |
| land cells with `FSDS < 1` or `TBOT` outside a physical range | sentinel forcing |
| `spinup_state` in `CaseDocs/lnd_in` before submitting an AD case | an AD stage that is not AD |
| `TOTSOMC` ratio across the AD-to-final handoff | `exit_spinup` failing to fire |
| `HDM` mean non-zero when fire is on | a silently failed forcing read |
| annual output for at least the first 30 AD years | collapse events invisible inside 20-year means |

## 11. Reproducing any of this

Everything comes from the `h1` PFT-vector history files (`hist_dov2xy = .false.`),
which exist for both spin-ups and the transient at both resolutions. A
50-variable screen of gridcell-mean `h0` fields found nothing; one `h1` read made
the cause obvious. When a gridcell-average field looks inexplicably low, go to
`h1` first.

`compare_ad_hdm_test.py` in this directory produces the section 5 table.

Four traps cost time here:

- The AD year-0001 `h1` file is the cold start with LAI 0 everywhere, so it must
  be excluded from any "first year stranded" test.
- `PCT_CROP` and `PCT_NATVEG` in the landuse timeseries file are static 2-D
  fields, not time-varying; indexing them by a time step silently broadcasts one
  latitude row.
- `netCDF4` applies `scale_factor` itself, so applying it again to the
  cpl_bypass forcing silently scales precipitation by 2.7e-06.
- `ATM_DOMAIN_PATH` is empty in this case lineage and `ATM_DOMAIN_FILE` is the
  bare name `domain.nc`, which GETFIL resolves against RUNDIR. A cloned case
  with a fresh RUNDIR dies in 22 seconds on `GETFIL: FAILED to get /domain.nc`
  until the file is staged or symlinked across.
- A `--keepexe` clone still has `BUILD_COMPLETE` reset to `FALSE` by
  `case.setup --reset`, and `case.submit` then refuses with "Build complete is
  not True". The executable is untouched; set `BUILD_COMPLETE=TRUE` and
  `SMP_VALUE` back to the source case's values rather than rebuilding.
- `xmlchange` splits its argument on commas, so
  `BATCH_COMMAND_FLAGS='... --exclude=blc051,blc052'` is truncated to `blc051`
  and errors with "Expecting a key value pair". Edit the XML directly.
- `BATCH_COMMAND_FLAGS` lives in `env_workflow.xml`, not `env_batch.xml`.
  Editing the latter appears to succeed and changes nothing.
