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

## Current evidence in brief

Reported pine low-LAI fractions are 9.1% at 4 km and 78.1% at 0.5 degrees.
Evergreens show much stronger persistent stranding than deciduous PFTs.
Evergreen phenology lacks a seasonal storage-to-leaf flush, which can hinder
re-establishment; this does not by itself explain all low-LAI states. An 80-year
cold-start experiment using the corrected HDM reader reduced pine stranding
from 8.9% to 0.9%. Coastal forcing mappings have also been repaired and checked
by replaying nearest-neighbour selection, but the combined vegetation response
has not been measured. The remaining 405 non-sentinel pine patches represent
about 0.6% of the pine population studied; their cause remains unresolved.
The 0.5 degree case never enabled AD and ended final spin-up far from soil-carbon
equilibrium. Corrected AD settings must be verified in each rebuilt case.

This record distinguishes configuration errors, measured outcomes and hypotheses;
it does not establish that every low-LAI patch will disappear.

## Where to look for what

| you want | section |
|---|---|
| what the symptom looks like, with numbers | 1 |
| the mechanism, from source | 2 |
| why 4 km and 0.5 degrees failed for different reasons | 3 |
| why the 0.5 degree chain is worse than the dieback alone | 4 |
| the experiment supporting the 4 km diagnosis | 5 |
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
Broadleaf evergreen shrub does the same. Deciduous PFTs do not show comparable widespread stranding; small low-LAI
fractions occur in section 5.

| | 4 km chain | 0.5 degree chain |
|---|---|---|
| pine patches stranded | **9.1%** | **78.1%** |
| broadleaf evergreen shrub | collapsed | 100% |
| every deciduous PFT | unaffected | unaffected |

Three properties make it distinctive.

**Binary, not graded.** At 4 km AD year 201: 9.0% of pine patches below LAI
0.01 and 90.9% above 1.0. The previously reported intermediate fraction
of 0.5% needs a denominator/bin audit: those values summed to 100.4%. At 0.5 degrees: 77.9% below 0.01, the
rest healthy, nothing between, median exactly 0.000 - while not one oak patch is
below LAI 0.5.

**One-way.** 26 transitions from stranded (LAI < 0.5) back to healthy
(LAI > 1.5) across 38 consecutive history outputs spanning ~800 model years and
63,000 patches.

**Set early, then frozen.** At 4 km the stranded fraction reads 1.0% in the
years 1-20 mean, 6.6% for 21-40, 8.9% for 61-80, then locks at 9.0-9.1% through
441 years of final spin-up and all 174 transient years. So the outcome is
settled inside the first eighty AD years and never moves again. Note these are
20-year means, not snapshots - which window a patch first shows up in is not
when it collapsed, see section 6.

**Exactly the evergreen PFTs.** Of the seven PFTs present in this domain, the
two with `evergreen = 1` in `clm_params.nc` are affected and the five with
`season_decid` or `stress_decid` do not show comparable widespread stranding. This does not mean every
deciduous patch has high LAI.

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
season. This supplies leaves independently of current leaf area when storage
and onset conditions permit; exhausted reserves can still prevent recovery.
Lack of evergreen onset alone does not prove every near-zero state is absorbing.

This explains the PFT selectivity, the binary distribution and the one-way
behaviour. It does not by itself explain what pushes a given patch over, nor
exactly what holds a stranded patch where it sits - see sections 3 and 7.

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

Fuel receives an extra nine times dead stem carbon. The factor of ten enters
selected deadwood burning/mortality terms, not every leaf or vegetation loss flux. Together these affect fire losses, giving ~1e-6
gC/m2/s fire loss against ~1e-8 at 0.5 degrees.

Supporting evidence at 4 km: `COL_FIRE_CLOSS` is 2.95x higher in the dying
cohort pre-mortem, 13.1% of their standing vegetation carbon burned per year
against 2.8% for survivors, and death rate rises 0.1% / 0.4% / 2.8% / 6.2% /
31.0% across fire quintiles. It survives stratification - within temperature and
sand strata the gradient holds in 7 of 8 strata, partial rank correlation 0.171.

**The corrected-reader experiment strongly supports this diagnosis** - see
section 5 and its source-version caveat.

### 0.5 degrees: nitrogen limitation, from an AD spin-up that was never AD

`20260831_seus_halfdeg_ad_spinup` has `spinup_state = 0` and no
`-bgc_spinup on` in `ELM_BLDNML_OPTS`. It ran with normal decomposition despite
the name. Consequence at year 21:

| run | FPG | FPI | SMINN | TOTSOMC | HR |
|---|---|---|---|---|---|
| 4 km AD | **1.000** | **1.000** | 0.090 | 459 | 9.4e-06 |
| 0.5 deg | **0.678** | 0.406 | 0.021 | 118 | 1.5e-06 |

The 4 km case uses `nyears_ad_carbon_only = 25`; its years-1-20 FPG of 1
cannot be attributed to abundant mineral N from AD, because that window is
inside the carbon-only phase. N limitation resumes in year 26 in this case;
AD supplies P (`suplphos = 'ALL'`), while final spin-up enables N and P limitation.
The missing AD setting and early N downregulation at 0.5 degrees are confirmed.
Their causal contribution to evergreen stranding needs a correctly configured
rerun; it has not yet been isolated experimentally.

Fire there was two to three orders of magnitude lower than 4 km, and it still
lost eight times as much pine. **Less fire, far more loss** - which is why fire
cannot be the general cause.

**How it was missed.** A search of prior session transcripts finds
`-bgc_spinup on` in exactly one place, a July 2026 script for the 4 km chain, as
`./xmlchange --append ELM_BLDNML_OPTS="-bgc_spinup on"`. It appears in neither
session that built the 0.5 degree cases. Nothing complains when it is absent:
the case builds, runs 201 years, and writes files named `ad_spinup`.

## 4. The 0.5 degree chain has a larger problem than the dieback

Because the earlier stage was not AD, no AD-exit rescaling was expected at
the handoff. This is not a separate failure to add carbon. In
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

AD pools are expected to be smaller under accelerated turnover. On exit, each
relevant pool is transformed using its acceleration factor and environmental
scalar. The observed 22x total change is case-specific, not a required ratio
or an equilibrium target for another resolution. The lack of final convergence
below is direct evidence of inadequate initialization at 0.5 degrees.

Convergence at the end of each final spin-up:

| | end TOTSOMC | end drift | verdict |
|---|---|---|---|
| 4 km | 16960 | **0.8% / century** | converged |
| 0.5 deg | 6752 | **13.0% / century** | far from equilibrium |

Thus the 0.5 degree chain has inadequate soil equilibration as well as
evergreen stranding, and the
transient plus seven future scenarios all inherit it.

## 5. Experiment: job 522373

`20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup` is a
clone documented as retaining the original inputs, PE layout and namelist,
using a newer E3SM source with corrected HDM reading. Other source changes
require the attribution caveat below. 80 model
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

**The large stranding reduction is concentrated in evergreens.** Mean LAI
also increases for deciduous PFTs, whose rounded stranded fractions are unchanged:

| PFT | ctrl LAI | expt LAI | ctrl stranded | expt stranded |
|---|---|---|---|---|
| needleleaf evergreen temperate | 1.623 | 1.940 | **8.9%** | **0.9%** |
| broadleaf evergreen shrub | 0.496 | 1.080 | **63.2%** | **22.6%** |
| broadleaf deciduous temperate tree | 2.544 | 2.757 | 0.3% | 0.3% |
| broadleaf deciduous temperate shrub | 8.398 | 9.134 | 0.7% | 0.7% |
| C3 grass | 5.372 | 5.694 | 0.3% | 0.3% |
| C4 grass | 5.666 | 7.079 | 0.0% | 0.0% |

Domain carbon and productivity increase in this experiment; these changes
do not establish observational accuracy or final equilibrium. Fire falls to 40% of the
control and everything else moves modestly upward in the expected direction:
TOTSOMC +15%, TOTVEGC +9%, GPP +7%, NPP +9%, TLAI +10%, SMINN +16%, FPG 0.949 to
0.969. These are experiment-control changes, not measured observational biases.

Reported NDEP values are 1.99e-08 and 1.98e-08, about 0.5% apart, not equal
to three significant figures. A calendar-year fix also landed between source
versions. HDM is strongly supported as the main driver, but strict single-change
attribution requires a source/executable audit or a matched-build HDM-only test.
Similar domain means do not prove every other source change was inactive.

### Conclusion

**The corrected-reader experiment removes most observed 4 km pine stranding.** It cuts the permanent
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

**Group B remains unexplained:** 405 pine patches, concentrated in south
Florida, do not show the identified ocean-sentinel forcing problem. Below 26 N,
42.4% of pine patches are reported stranded. Fire, resource limitation,
establishment and other input/model issues remain candidates; none has been
established as the cause of this residual.

**About 0.6% is arithmetic, not a combined-fix outcome:**
`(598 - 193) / 68773 = 0.589%`. Job 522373 used corrected HDM with the unfixed
mapping. Job 522626 is documented as using the original HDM executable with the
corrected mapping. No combined-fix vegetation result is documented here.
Compare matching averaging windows and continue checking through full AD and
final spin-up. Stability across three windows in 80 years does not prove
stability through the completed chain.

**Count audit pending:** 194 zero-GPP land cells, 193 sentinel-associated pine
patches and 193 changed land-cell mappings are reported. Patch and gridcell
counts differ, but that alone does not explain the 194-versus-193 gridcell
mismatch. Reconcile IDs and masks before claiming all affected cells are covered.

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
happens - configured for 30 years with `hist_nhtfrq = -8760, hist_mfilt = 30`, annual
output, on 20 nodes of `parallel`. It also adds `LEAFN`, `FROOTN`, `LIVESTEMN`,
`LIVECROOTN`, `XSMRPOOL`, `LEAFC_ALLOC`, `LEAFC_LOSS` and `LEAFC_TO_LITTER` to
both tapes. Section 7 explains the additional fields needed for respiration.

## 7. What is still open

### Zero-carbon patches and surviving low-LAI patches must be separated

The former interpretation treated cohort means (`LEAFC = 0.092 gC/m2`,
`NPP = 0.187 gC/m2/yr`) as a typical stranded plant. That interpretation and
the inferred ~1250-year individual decay timescale are withdrawn pending a
patch-level audit. Many zeros mixed with a few surviving patches can yield
small positive means without any plant occupying that state.

An independent strided check of 4 km final-spin-up h1 stamped 0441 selected
1,874 pine patches (vegetation type 1, natural landunit, gridcell weight > 0.05).
Of 160 with TLAI < 0.5, 159 had zero LEAFC, GPP, NPP, AR and CPOOL; only one
retained positive leaf carbon. Of the 159 zeros, 158 were already zero in the
matching 0201 record. The surviving patch had LEAFC about 42.13 gC/m2. This is a
sample with its own mask, not a census or an exact reconstruction of the earlier
cohort. Local ignored artifacts: `outputs/leaf_budget_stride37_0441.json` and
`outputs/leaf_budget_followup_summary.json`.

Audit the full cohort with stable patch IDs, separating zero LEAFC/GPP,
positive low-LAI and healthy patches. Compute transitions and budgets within
each class. Ratios of cohort means cannot establish an individual plant's
respiration burden or a stable low-biomass equilibrium.

### Respiration and allocation corrections

In the inspected RD non-crop branch, `VegetationDataType.F90` defines
`AR = MR + GR + XR` and NPP = GPP - AR. The residual AR-MR-GR is therefore
**XR**, not an unexplained XSMRPOOL term. `MaintenanceRespMod.F90` computes XR
from CPOOL, `br_xr` and temperature; `CarbonStateUpdate1Mod.F90` subtracts it
from CPOOL. Diagnose XR, CPOOL and temperature directly.

The inspected pine parameter `stem_leaf = -1` invokes NPP-dependent allocation
in `AllocationMod.F90`. A fixed leaf share of 24.6% is not the implemented rule.
Leaf replacement must use actual allocation and total losses, including litter,
background mortality, fire and harvest, with other transfers and numerical
truncation included where applicable.

Job 522626 is documented as an annual diagnostic with tissue N pools,
XSMRPOOL, LEAFC_ALLOC, LEAFC_LOSS and LEAFC_TO_LITTER. Current scheduler status
was not rechecked in this edit. These fields help the leaf budget, but XSMRPOOL
alone does not diagnose XR. Verify availability of XR, CPOOL and individual
tissue respiration before treating the run as a complete respiration diagnosis.
Annual means cannot resolve every within-year limitation or collapse event.

### Recovery and prevention

Evergreen phenology lacks a seasonal re-flush; PrecisionControlMod can truncate
extremely small leaf carbon to zero. Deciduous recovery requires reserves and
suitable onset conditions. The inspected land-cover pathway seeds an expanding
patch (`dwt > 0`), not any arbitrary area change. Its role in the reported
0.5 degree transient recovery from 78.1% to 9.9% remains a hypothesis until
seed fluxes and patch transitions are checked.

The selected plan is corrected inputs/configuration and cold-start reruns,
with per-PFT checks after each stage. A compatible healthy restart, a carbon
floor or restart-pool edits would be separate experiments, not validated
remedies or requirements for the current rerun.

## 8. Explanations advanced and rejected

Recorded so that none of them comes back second-hand as established. Each was
argued from data and then contradicted by better data.

1. **Positive mean NPP rules out carbon shortage.** A positive multi-year or
   cohort mean cannot rule out individual or seasonal deficits; use patch budgets.
2. **Fire is the root cause.** The 0.5 degree chain has two to three orders of
   magnitude less fire and eight times more loss. Fire is a trigger, at 4 km.
3. **`spinup_mortality_factor` is irrelevant.** It also multiplies fire
   mortality and inflates fuel load in `FireMod.F90`.
4. **A low mean implies uniformly slow establishment.** The distribution is
   bimodal. This does not make a different-resolution, differently configured
   run a controlled experiment.
5. **Tissue carbon ratios establish the respiration mechanism.** Earlier cohort
   ratios require reanalysis after separating zeros; tissue N and temperature
   are also needed to explain maintenance respiration.
6. **Fixed allometry explains slow decline.** Allocation is dynamic and the
   ~1250-year estimate came from mixed means, not individual-patch trajectories.

Two method lessons behind them. Items 1 and 4 are the same error, **a mean taken
over a bimodal population**. Item 3 came from **stopping a source search at the
first plausible module**.

## 9. Impact, if nothing is changed

Counterfactual: give each stranded patch the mean carbon of healthy pine in the
same temperature band, at its own PFT weight.

| | GPP bias | vegetation C bias | affected cells |
|---|---|---|---|
| whole SEUS domain | 2.1% low | 2.4% low | 7.2% |
| Georgia box | 3.1% low | 3.9% low | 8.7% |
| **Florida box** | **11.3% low** | **16.8% low** | **38.2%** |
| affected cells themselves | 28% low | 39% low | - |

These are counterfactual estimates using matched healthy pine, not measured
biases against observations or guaranteed rerun improvements. They also do not
quantify the 0.5 degree soil disequilibrium.

Existing results may support provisional poster material with explicit regional
and initialization limitations. Shared erroneous initial states do not guarantee
cancellation in scenario differences: missing vegetation changes responses to
climate, harvest and land-use change. Regional carbon, biomass validation and
scenario sensitivities need reassessment against corrected runs.

Minimum action without rerunning: mask or flag the affected cells in any map or
regional total and state the limitation. They are reproducible from h1 output as
pine patches with TLAI < 0.5 over the stated history averaging window.

## 10. Rerun plan

The identified corrections support rebuilding. HDM has an 80-year experimental
check; mapping repair has a static selection check; AD must be enabled per case.
Combined vegetation outcomes and final convergence remain unverified.

### Prerequisites and verification status

| fix | where | status |
|---|---|---|
| HDM reader corrected for custom grid/calendar handling | `lnd_import_export.F90`, patched 2026-07-17 | in the current `SRCROOT` |
| `zone_mappings.txt` free of ocean sentinels | 5 tables under `Daymet_ERA5_TESSFA2/cpl_bypass_full` | done 2026-09-10, verified |
| `-bgc_spinup on` for any AD case | `ELM_BLDNML_OPTS` | must be set per case, see below |

Section 5 supports substantial improvement from the corrected-reader run, not
proof that the combined fixes eliminate low LAI or restore observed GPP.
Verify each case's actual executable and forcing paths.

### Order: 0.5 degrees first

It is the more broken chain and by far the cheaper one. Its `NTASKS_LND` is 571
against 4 km's 2560, on a domain with roughly two orders of magnitude fewer
gridcells. These task counts are planning values; measure runtime and
convergence for the selected layout before promising completion dates.

### Chain A - 0.5 degrees, rebuild entirely

The 0.5 degree final spin-up ended at 6752 gC/m2 with 13.0% soil-carbon drift
per century: direct evidence of inadequate equilibration. The 4 km stock is a
comparison, not a target proving a sevenfold deficit. Rebuilding is the chosen
plan to address both establishment and soil initialization.

1. **AD spin-up, initially 200 years, cold start.** Set
   `./xmlchange --append ELM_BLDNML_OPTS="-bgc_spinup on"`.
   Verify `spinup_state = 1`, carbon-only duration, nutrient settings and actual
   executable/configuration. Check PFT establishment and pool evolution before
   ending the stage; 200 years is an initial duration, not proof of convergence.
2. **Final spin-up from AD restart.** Verify restart spinup metadata and
   per-pool AD-exit transformations with applicable factors/scalars. Do not
   require a particular total TOTSOMC ratio. Use end drift below about 1% per
   century as one screening criterion, alongside regional/PFT health and other
   pools; document the averaging interval and extend if needed.
3. **Transient 1850-2023**, then **seven future scenarios**, after stage checks.

### Chain B - 4 km, rebuild from the AD stage

The final spin-up and everything downstream inherit the stranded evergreens, so
the rerun has to start at AD. Do not restart from any existing 4 km restart file.

1. **AD spin-up, 200 years, cold start**, on the current source. Configuration is
   otherwise the reference one - fire on, no `use_nofire`, `spinup_state = 1`,
   `spinup_mortality_factor = 10` and `nyears_ad_carbon_only = 25` as
   reference-case settings; 25 is not the general namelist default. Measured cost for the original: 2h40m per 20 years on 12 nodes,
   26.7 h for 200 years by extrapolation; benchmark the 20-node layout.
   **Checks:** use the first complete averaging window, excluding the initial
   year-0001 record, and repeat through AD and final spin-up:
   - Compare HDM spatial values to inputs; mean near 5.1 is a reference.
   - Verify no selected ocean sentinels; inspect temperature and annual-mean
     radiation, including land cells with FSDS < 1.
   - Report low-LAI fractions, exact zeros and surviving low-LAI patches by PFT,
     especially in south Florida. The HDM-only years-1-20 value of 0.4% is a
     comparison, not a hard combined-rerun acceptance threshold.
2. **Final spin-up.** Check metadata and per-pool AD-exit transformation, then
   convergence and regional/PFT health as above.

3. **Transient 1850-2023.** Measured cost: 66.4 h on 12 nodes for 174 years.
4. **Future scenarios**, which pick up the fixed `future_clim/ssp*` tables
   automatically.

### Expected outcome, and what it is based on

**Measured:** corrected-reader pine stranding falls from 8.9% to 0.9% in the
years-61-80 window. Shrub stranding remains 22.6% and needs separate assessment;
pine percentages must not be generalized to all evergreens.

**Not measured:** both fixes together or a completed corrected chain. The 0.6%
pine figure is the non-sentinel subset in the existing experiment, not a
prediction guaranteed after rerunning. Mapping repair removes the identified
invalid selection; vegetation and Florida carbon improvements require output
verification using matching windows, masks and denominators.

The rerun does not change evergreen phenology. It addresses confirmed errors,
while the cause and eventual outcome of the remaining 405 pine patches remain
open. Removing errors alone does not demonstrate observational GPP accuracy.

### Standing checks for any future spin-up

Cheap, and each maps to something that actually went wrong here.

| check | catches |
|---|---|
| per-PFT LAI from the `h1` tape after spin-up | the entire dieback, which a 50-variable gridcell-mean screen missed |
| land cells with `FSDS < 1` or `TBOT` outside a physical range | sentinel forcing |
| `spinup_state` in `CaseDocs/lnd_in` before submitting an AD case | an AD stage that is not AD |
| restart metadata and per-pool AD-exit transformations | incorrect stage handoff |
| spatial HDM values and range against inputs | incorrect forcing read |
| annual output for at least the first 30 AD years | collapse events invisible inside 20-year means |

## 11. Reproducing any of this

Everything comes from the `h1` PFT-vector history files (`hist_dov2xy = .false.`),
which exist for both spin-ups and the transient at both resolutions. A
50-variable screen of gridcell-mean `h0` fields found nothing; one `h1` read made
the cause obvious. When a gridcell-average field looks inexplicably low, go to
`h1` first.

`compare_ad_hdm_test.py` in this directory produces the section 5 table.

The following traps cost time here:

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
