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
was measured on 2026-09-11 and is reported in section 5: the 193 coastal patches
recover, the 405 do not. Those 405 are about 0.6% of the pine population studied
and 0.42% of domain pine carbon, and they are now an accepted, masked limitation
rather than an open defect.
The 0.5 degree case never enabled AD and ended final spin-up far from soil-carbon
equilibrium. Corrected AD settings must be verified in each rebuilt case.

Added 2026-09-10, from jobs 522626 and 522812: the mapping repair is now
verified in a running model, with zero flagged land cells and positive GPP at
all 194 previously affected cells. Under the **old** HDM the 405 residual
patches establish and then decline, with about five times the fire event
frequency of healthy pine starting ten years earlier; that association is not
an independent causal result and does not describe the post-fix regime. Excess
respiration is excluded as the initiator of that early decline. Section 7 lists
what remains open.

This record distinguishes configuration errors, measured outcomes and hypotheses;
it does not establish that every low-LAI patch will disappear.

## Where to look for what

| you want | section |
|---|---|
| what the symptom looks like, with numbers | 1 |
| the mechanism, from source | 2 |
| why 4 km and 0.5 degrees failed for different reasons | 3 |
| why the 0.5 degree chain is worse than the dieback alone | 4 |
| the experiments supporting the 4 km diagnosis | 5 |
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
440 years of final spin-up and all 174 transient years. So the outcome is
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

### Measured in the same gridcells, under the same fires

Added 2026-09-11 from the AD rerun, job 523210. Pine and broadleaf deciduous
temperate tree both occupy all 405 residual gridcells and burn in the same
fires, so the comparison controls disturbance, climate and soil exactly. Annual
means, states in gC/m^2 and fluxes in gC/m^2/yr:

| model year | pine LAI | storage | storage to leaf | CPOOL to leaf | leaf fire loss | | decid LAI | storage | storage to leaf | CPOOL to leaf | leaf fire loss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 1.78 | **0.00** | **0.00** | 171.8 | 0.9 | | 1.03 | 156.8 | 63.0 | **0.00** | 0.3 |
| **7** | 1.60 | **0.00** | **0.00** | 99.6 | **53.1** | | 1.61 | 204.5 | 94.0 | **0.00** | 2.8 |
| 9 | 0.92 | **0.00** | **0.00** | 55.5 | 13.7 | | 2.12 | 217.3 | 123.3 | **0.00** | 13.6 |
| **17** | 1.10 | **0.00** | **0.00** | 66.4 | **63.6** | | 2.05 | 219.1 | 159.2 | **0.00** | **60.8** |
| 19 | 0.53 | **0.00** | **0.00** | 36.6 | 6.4 | | 1.87 | 198.7 | 105.3 | **0.00** | 4.6 |
| 30 | 0.06 | **0.00** | **0.00** | 2.0 | 3.8 | | 1.41 | 155.4 | 88.5 | **0.00** | 14.6 |
| 49 | 0.03 | **0.00** | **0.00** | 3.0 | 0.1 | | 1.73 | 163.3 | 95.4 | **0.00** | 2.3 |

In model year 17 the two PFTs lose almost the same leaf carbon to fire, 63.6
against 60.8. Everything after that differs.

**Pine's `LEAFC_STORAGE` and `LEAFC_XFER_TO_LEAFC` are exactly 0.00 in every
year, without exception.** Its only leaf source is `CPOOL_TO_LEAFC`, carbon
fixed in the current year. Deciduous is the mirror image: `CPOOL_TO_LEAFC` is
exactly 0.00 every year, and it rebuilds from a storage pool of 160 to 260 that
releases 90 to 160 per year **regardless of how much leaf area is currently
standing**.

The ratchet is visible in pine's `CPOOL_TO_LEAFC`: 171.8, then 99.6 when the
year-7 fire lands, 55.5, recovering to 106 by year 16, then 66.4 after the
year-17 fire, 36.6, 22.3, 2.0. Less leaf gives less photosynthesis gives less
carbon to allocate to leaf. Deciduous drops from 84.6 to 60.1 at the same fire
and is back to 48.2 the next year on a 91.7 flush.

This is the section-2 mechanism measured rather than inferred from the source.

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

## 5. Experiments: job 522373, and jobs 522626 / 522812

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
through 440 years of final spin-up and 174 transient years.

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
corrected mapping. **Superseded 2026-09-11**: the combined-fix result now exists
and is in the subsection at the end of this section.
Compare matching averaging windows and continue checking through full AD and
final spin-up. Stability across three windows in 80 years does not prove
stability through the completed chain.

**Count audit pending:** 194 zero-GPP land cells, 193 sentinel-associated pine
patches and 193 changed land-cell mappings are reported. Patch and gridcell
counts differ, but that alone does not explain the 194-versus-193 gridcell
mismatch. Reconcile IDs and masks before claiming all affected cells are covered.

### 522626 and 522812: annual diagnostic under the old HDM

Kept separate from the HDM-fix experiment above on purpose. `20260910_ADdiag_annual_ICB1850CNRDCTCBC_ad_spinup`
is a `--keepexe` clone of the ORIGINAL AD spin-up, so it runs the **pre-2026-07-17
HDM executable** with human population density at zero and fire unsuppressed. It
is also the **first run to read the repaired `zone_mappings.txt`**, the tables
having been rewritten between 15:24 and 15:44 on 2026-09-10 and the job starting
at 16:18. So it tests the mapping fix while its stranded fractions stay control
values. 30 model years, annual output on both tapes, 20 nodes, 02:17:54,
COMPLETED 2026-09-10. Analysis job 522812; `analyze_ad_annual_522626.py`.

**Headline.** The 405 residual locations carry more frequent and much earlier
fire threshold events, together with a markedly higher rate of sustained
decline. Per-patch annual pairing supports a temporal association between fire
and decline. A high event base rate, overlapping response windows and
environmental confounding all limit how far that can be read as cause. None of
it represents the decline process after the HDM fix.

| group | n | established, median yr | fire events per patch, mean | first fire event, median yr | sustained declines |
|---|---|---|---|---|---|
| 405 residual | 405 | 7 | 10.3 | 8 | 404 |
| 193 coastal, mapping repaired | 193 | 7 | 2.0 | 18 | 15 |
| healthy sample | 2000 | 7 | 1.9 | 18 | 7 |

Every patch in all three groups reached LAI 1.0 at some point, so none failed to
establish. The **median** establishment year is 7 in each group; the individual
years are not identical and the spread was not audited patch by patch.

**Coastal mapping repair, verified in a running model.** From annual record 2
onward, zero land cells out of 75,920 read a flagged forcing value, against 194
before. All 194 previously affected cells show positive GPP, minimum FSDS about
160 W/m2 and maximum TBOT about 25 C, against a constant FSDS of -1111 and TBOT
of 122.9 before. The first annual record carries FSDS identically zero on every
land cell; that is a cold-start artifact of the first history interval, not
sentinel forcing, and it is excluded rather than counted.

**The 194 against 193 count is reconciled.** Of the 194 flagged land cells, 193
host a selected pine patch and 1 does not, because the patch mask requires PFT
1, natural landunit and gridcell weight above 0.05. The 598 low-LAI pine patches
split exactly into 193 plus 405.

**What the 193 repaired patches do, and what that does not settle.** Their fire
frequency now matches the healthy sample, 2.0 events per patch against 1.9, with
the first event at median year 18 in both. Their sustained decline rate does
not match: **15 of 193, 7.8%, against 7 of 2000, 0.35%**. The forcing and
productivity side of the coastal repair passes. Whether the vegetation response
of the two groups is equivalent is a separate question and is not settled here.

**Per-patch pairing, and why the count is weak evidence.** For the 405: 397 have
a fire in a year before the decline, 7 have one in the same year and are counted
`same_year_order_unresolved`, none has fire only after, and 1 shows no sustained
decline. The gap between the decline year and the most recent preceding fire has
all three quartiles at 1 year.

That 397 out of 404 is close to uninformative on its own. At a mean of 10.3
events in 30 years, some earlier fire is nearly certain for any decline date, and
a fire in the immediately preceding year has a base rate near one in three from
frequency alone. The between-group contrast in the table carries more weight
than the pairing count. Even that contrast is an association, not an independent
dose-response result: the groups were defined by final low LAI in a **different**
simulation, and environmental conditions can drive fire and decline together.

**Leaf carbon retained after a fire event**, over the following three years,
averages 0.72 for events before a patch's decline and 0.50 for events after it.
A ratio below 1 shows net loss following fire, not that fire caused all of it.
At this event frequency the three-year response windows also overlap between
successive events, so the values are not independent.

**Timing of the decline.** Declines cluster in years 9 and 18 and 19 for the 405,
with 356 of 404 before the carbon-only phase ends at year 25. The 15 coastal and
7 healthy declines all fall at about year 27, which coincides with nitrogen
limitation resuming at year 26; coincidence in time is not attribution, and the
run ends at year 30, too early to say whether that decline recovers or persists.

**Excess respiration is excluded as the initiator of the early decline.** XR,
recovered exactly as `AR - MR - GR` for the non-crop `nu_com='RD'` branch, is
zero to numerical noise of order 1e-14 through year 26, and `CPOOL` is zero over
the same span, as expected inside the carbon-only phase. The 405 decline over
years 8 to 20, when XR is zero. From year 27 XR appears, and the healthy sample
carries roughly ten times more of it than the residual group, so it tracks having
carbon rather than losing it. This bounds **excess** respiration only.
Maintenance and growth respiration remain present and are reported as MR and GR.

**The lumped leaf loss term follows the fire years.** Non-litterfall loss,
`LEAFC_LOSS - LEAFC_TO_LITTER`, is about 3% of total leaf loss in quiet years,
36% in year 8 and 49% in year 18. Splitting fire from background mortality still
requires `M_LEAFC_TO_FIRE`, `M_LEAFC_TO_LITTER_FIRE` and `M_LEAFC_TO_LITTER`,
all registered `default='inactive'` and absent from this case.

**Two analysis defects found and fixed between 522807 and 522812**, recorded
because both would have produced confident wrong numbers. A plain "first year
below LAI 0.5" returned year 1 for every patch in all three groups, because a
cold start puts everything below any threshold in year 1. The decline is now
dated against each patch's own running peak, requires three consecutive years
below half of it, and pairs fire event by event rather than by the single
largest fire of the record.


### The AD rerun with both fixes: jobs 522930 and 523140

The production rerun, `20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup`,
30 nodes, 3840 ranks, cold start, corrected HDM reader **and** repaired
`zone_mappings.txt` together for the first time. Analysis job 523199 reads only
the first closed segment file, model years 1 to 49. The run continues to year
200; everything here is provisional on that.

**The two populations end up in opposite places.**

| group | TLAI at model year 49 | verdict |
|---|---|---|
| 193 coastal, forcing repaired | **1.962** | recovered; healthy control is 1.977 |
| 405 residual | **0.032** | still declining, essentially as before |

**Why the HDM fix cannot help the 405.** Their 1850 human population density,
read from the model's own `HDM` field:

| group | median HDM | mean | fraction below 0.5 |
|---|---|---|---|
| 405 residual | **0.048** | 0.051 | **100%** |
| 193 coastal | 0.745 | 1.236 | 23% |
| healthy pine | **4.162** | 4.926 | 5.6% |

Every one of the 405 sits where population density is about one eighty-seventh
of the healthy-pine median. Population drives both human ignition and
suppression, so a corrected reader delivers them what a broken reader delivered
everywhere: nearly nothing. The HDM repair is real and domain-wide, and
physically inert in exactly these places. That is also why job 522373, which had
the HDM fix, left this residual behind.

**The leaf budget closes exactly.** Year-end state from the instantaneous `h2`
tape against the integrated fluxes gives a closure residual of **0.000 gC/m^2 in
every year**, to machine precision. No missing term, harvest zero, truncation
negligible at these magnitudes. That licenses the split below, which job 522626
could not make.

Columns are group means of per-patch values. **The last column is the mean of
each patch's own `fire / total loss` ratio, not the ratio of the two group means
beside it**, so it does not equal column 4 divided by column 3. Both are
legitimate; the per-patch mean is reported because it weights every patch
equally rather than letting the heaviest-burning patches set the ratio.

| model year | state change | total loss | fire | background mortality | litterfall | fire share, per-patch mean |
|---|---|---|---|---|---|---|
| 6 | +55.1 | 116.7 | 0.9 | 3.4 | 112.5 | 0.7% |
| **7** | **-57.6** | 157.1 | **53.1** | 3.0 | 101.0 | **31.4%** |
| 10 | +29.1 | 68.0 | 1.5 | 1.9 | 64.6 | 3.6% |
| **17** | **-68.8** | 135.2 | **63.6** | 2.1 | 69.5 | **37.3%** |
| 25 | -20.9 | 43.2 | 18.1 | 0.7 | 24.4 | 29.7% |

The two deepest declines are the two fire years. Background mortality is a
rounding term throughout. Litterfall is always the largest single flux, but it
scales with standing leaf carbon, so it is turnover rather than a driver; what
changes in a decline year is fire.

**Per-PFT outcome, by region.** Fraction not healthy, meaning zero leaf carbon
plus surviving low-LAI, on 20-year windows built from annual records.

| population | years 1-20 | years 21-40 | years 41-49 | old chain, final |
|---|---|---|---|---|
| pine, whole domain | 0.14% | 0.52% | **0.55%** | 9.0% |
| pine, Florida box | 1.29% | 4.77% | 5.00% | - |
| pine, south of 26 N | 23.5% | 40.5% | **40.7%** | 42.4% |
| broadleaf evergreen shrub, whole domain | 13.2% | 2.6% | **2.4%** | 22.6% under HDM-only |
| every deciduous PFT, whole domain | 0% | 0% | 0% | - |

The domain number improves by more than an order of magnitude. South of 26 N is
essentially unchanged. Reporting only the first row would be the error this
record has warned about throughout. The 41-49 window is nine years, not twenty.

**Where the 405 actually are.** Two clusters, not one. The earlier
characterisation as south Florida was incomplete.

| cluster | n | extent |
|---|---|---|
| south Florida, Big Cypress and the Everglades | **291** | 25.19 to 26.65 N, -81.35 to -80.65 |
| Florida Big Bend and panhandle coast | **114** | 29.19 to 30.10 N, -85.27 to -83.02 |

Map: `outputs/residual_405_map.png`, produced by
`plot_residual_405_map_local.py`. What both clusters share is that almost nobody
lived there in 1850.

### Decision, 2026-09-11: the residual is accepted as a quantified limitation

Area-weighted, over model years 41 to 49, which is what decides whether it
matters:

| region | pine area weight | stranded, area-weighted | pine vegetation carbon missing | healthy `TOTVEGC` baseline |
|---|---|---|---|---|
| whole domain | 27002 | **0.42%** | 0.42% | 1809.1 |
| Florida box | 4188 | 2.72% | 2.71% | 1736.5 |
| south of 26 N | **84** | 41.6% | 41.4% | 1599.0 |
| 25 to 27 N band | 291 | 20.4% | 20.1% | 1410.5 |

**How the carbon column is computed**, since a percentage of missing carbon
needs a stated counterfactual. Script:
`quantify_stranded_pine_impact.py` in this directory.

- Baseline is the **area-weighted mean `TOTVEGC` of healthy pine in the same
  region**, meaning every pine patch in that region with mean TLAI at or above
  0.5 over model years 41 to 49. It is not temperature-matched, and it is not
  the domain mean applied everywhere. The regional baselines differ, 1809 for
  the domain against 1410 in the 25 to 27 N band, which is why a regional
  baseline matters.
- Missing carbon is `stranded_area * healthy_baseline` minus the carbon those
  patches actually carry.
- The denominator is what the region would hold if the stranded patches sat at
  their regional healthy baseline, so the percentage is against a
  counterfactual total, not against the simulated one.
- It is total vegetation carbon, not leaf carbon.

⚠️ This is a **different baseline** from the counterfactual in section 9, which
matched healthy pine within the same temperature band. The two numbers are not
directly comparable. The regional baseline is the coarser of the two; it was
chosen because the decision it informs is regional reporting scope, not a bias
estimate against observations.

The 41.6% south of 26 N sits on a pine area weight of 84, which is 0.3% of the
domain total. So the large regional percentage and the small absolute
consequence are both true.

**The residual is accepted rather than chased further.** At 0.42% domain-wide it
is far below the model's own structural uncertainty and below the uncertainty in
the forcing and surface datasets. Another experiment to remove it does not
change any decision that depends on the domain or state scale.

**Where the results stay usable, and where they do not.**

- Usable: domain-wide and state-scale pine results, and all deciduous PFTs
  everywhere.
- Needs a stated caveat: the Florida box, at 2.7% of pine carbon missing.
- **Not usable without excluding the mask**: anything south of 26 N, anything
  specific to south Florida pine flatwoods, the Everglades or Big Cypress, and
  anything specific to the Big Bend and panhandle coast.
- **Management scenarios need particular care.** These gridcells hold almost no
  pine leaf carbon, so they cannot respond to reforestation, reduced harvest or
  any other treatment. In a scenario difference the signal is absent rather than
  cancelling, so a treatment whose target area overlaps either cluster will read
  systematically low.

**Mask file**, so this never has to be re-derived:

```text
/projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/stranded_pine_mask_SEUS_1_24deg.nc
```

Variables `stranded_pine` and `pine_present` on the 324 x 504 grid, with the
membership definition and the numbers above in the file's own attributes.
Written by `make_stranded_pine_mask.py` in this directory.

**The no-fire counterfactual is not scheduled, and its reach was overstated
earlier in this record.** It can test one thing only: whether removing fire
prevents the decline. It **cannot** judge whether the simulated fire frequency
or intensity is realistic. That needs observational or independent constraint,
for example burned-area products or published fire return intervals for south
Florida pine flatwoods, and no model-only experiment substitutes for it.

So the open question splits in two:

| question | what would settle it |
|---|---|
| does removing fire prevent the decline | the no-fire run, about 3 h on 30 nodes |
| is the simulated fire regime realistic | observations or an independent constraint, not a model run |

With the residual accepted, neither changes an action now. Both stay open and
documented. Run the first if a reviewer asks or if the regional result becomes
the deliverable; the second is required before any claim that the fire itself is
correct.

**Accepted is not the same as absent.** This is a quantified, bounded bias with
a mask attached, not a solved problem.

**Inference, labelled as such.** The two configuration errors are gone and what
remains is pine in genuinely unpopulated, fire-prone country. Whether that fire
is itself correct is not established here. If it is, the residual is not a
configuration bug but the section-2 absorbing state meeting a real disturbance
regime, and no input repair can remove it. Distinguishing "the fire is wrong"
from "the fire is right and recovery is broken" is exactly what the no-fire
counterfactual in the plan would test, and it is the first result that gives
that experiment a specific question.

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
better at 23 points spanning 440 years, but has the same blind spot below 20 years.

**Diagnostic run 522626 addressed this, and it has run.** See the new subsection
at the end of section 5 for what it settled. One statement this section
downgraded can now be made from annual data, for the old-HDM run only: the 405
residual patches do establish first and then decline, reaching a mean peak leaf
carbon of 190 gC/m2 before any sustained drop, so "they establish and then fail"
is measured rather than inferred in that run. Configuration below.


`20260910_ADdiag_annual_ICB1850CNRDCTCBC_ad_spinup` is a `--keepexe` clone of the
original AD spin-up - so the *unfixed* HDM reader, where the collapse actually
happens - configured for 30 years with `hist_nhtfrq = -8760, hist_mfilt = 30`, annual
output, on 20 nodes of `parallel`. It also adds `LEAFN`, `FROOTN`, `LIVESTEMN`,
`LIVECROOTN`, `XSMRPOOL`, `LEAFC_ALLOC`, `LEAFC_LOSS` and `LEAFC_TO_LITTER` to
both tapes. Section 7 explains the additional fields needed for respiration.

## 7. What is still open

### Status after jobs 522626 and 522812

Written so the two are not confused. Everything below refers to the 4 km chain.

**Settled.**

- The coastal mapping repair works in a running model: zero flagged land cells
  from annual record 2 onward, and positive GPP with physical TBOT and FSDS at
  all 194 previously affected cells.
- The 194 gridcell against 193 patch count: 193 of the 194 flagged cells host a
  selected pine patch, 1 does not.
- Excess respiration is not the initiator of the early decline, since XR and
  `CPOOL` are zero through year 26 while the 405 decline over years 8 to 20.
- Under the old HDM, the 405 establish first and then decline, and they carry
  roughly five times the fire event frequency of healthy pine, starting about
  ten years earlier.

**Not settled, and specifically not settled by these two jobs.**

- ~~Whether the 405 still decline once both fixes are active.~~ **Answered
  2026-09-11: they do**, reaching TLAI 0.032 by model year 49 against 1.977 for
  healthy pine, because their 1850 population density is about 0.05 and HDM
  suppression therefore cannot reach them. See section 5.
- Whether the fire that removes them is itself correct. This is now the live
  question and the one the no-fire counterfactual would answer.
- Whether fire causes the decline rather than accompanying it. The pairing count
  has a high base rate, the three-year response windows overlap at this event
  frequency, the grouping was defined by final low LAI in a different
  simulation, and environment can drive fire and decline together.
- ~~Whether the 193 repaired coastal patches are equivalent to healthy pine.~~
  **Answered 2026-09-11: yes in the rerun**, TLAI 1.962 against 1.977 for the
  healthy control at model year 49. The 7.8% against 0.35% decline-rate gap seen
  in job 522626 does not carry over to the run where their forcing is repaired
  from the start.
- What the year-27 decline seen in all three groups is. It coincides with
  nitrogen limitation resuming at year 26, which is not attribution, and the run
  ends at year 30, too early to tell a recoverable excursion from a persistent
  loss.
- ~~The split of fire from background mortality.~~ **Done**: the rerun carries
  the three fields and fire is 31 to 37 percent of leaf loss in decline years
  against 1 to 4 percent in quiet ones.
- ~~Strict per-year leaf carbon closure.~~ **Done**: the instantaneous `h2` tape
  closes the budget to 0.000 gC/m^2 per year.
- Whether the residual is stable through model year 200, and whether prognostic
  phosphorus at final spin-up re-strands anything. Both need stages that have
  not run.

**Updated 2026-09-11 by the AD rerun.** Both fixes now act in one run. Settled
since the list below was written: the combined vegetation outcome exists, the
193 coastal patches recover fully, the 405 do not and the reason is that their
1850 population density is near zero so HDM suppression cannot reach them, the
leaf budget closes exactly, fire is the proximate loss term in the decline
years at 31 to 37 percent of total leaf loss, and the pine-versus-deciduous
contrast is measured in the same gridcells rather than inferred from source.
Still open: whether that fire is itself correct, whether the residual is stable
to model year 200, and every later-stage question. The paragraphs below stand
except where the new subsection in section 5 supersedes them.

**How the two fixes stand.** Each has single-factor support. The HDM fix was
verified in job 522373: HDM reads correctly at a domain mean near 5.128 against
0.000 in the control, and pine stranding falls from 8.9% to 0.9%. The mapping
fix was verified in job 522626: zero flagged land cells and positive GPP at all
194 previously affected cells. What does not exist is a run with **both** fixes
active, so the combined vegetation state is unverified. That is a gap in joint
verification, not an absence of evidence for either fix.

**What the combined experiment will and will not settle.** It is the only way to
measure the combined vegetation outcome, and it supplies the per-PFT fire and
mortality fluxes that the residual diagnosis needs. It does not guarantee causal
attribution on its own: if the 405 largely recover, the mechanism that was
removing them is inferred rather than isolated, and if they do not, the
counterfactual in the plan becomes the next step.

The forward plan for all of these is [RERUN_VERIFICATION_PLAN.md](RERUN_VERIFICATION_PLAN.md),
and the case configuration is [AD_RERUN_CASE_CONFIG.md](AD_RERUN_CASE_CONFIG.md).


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

Job 522626 ran and completed; job 522812 analysed it. `XR` is not on its tape
but is recoverable exactly as `AR - MR - GR` for this non-crop `nu_com='RD'`
configuration, so no new run was needed. **Resolved for the early decline:**
excess respiration is not its initiator, since XR and `CPOOL` are both zero
through year 26 while the 405 decline over years 8 to 20. **Still open:**
this bounds excess respiration only. Maintenance and growth respiration are
present throughout and their contribution to the low-biomass state has not been
quantified; nor has any of this been repeated under the corrected HDM. Annual
means still cannot resolve within-year limitation or ordering.

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

**Measured 2026-09-11 for the AD stage**, see section 5; the completed chain
through final spin-up and transient is still outstanding. The 0.6%
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
