# Evergreen dieback in the SEUS spin-ups: status and open questions

Written 2026-09-09 for an independent review. Everything below is measured from
model output or read out of the E3SM source unless it says otherwise. Where a
claim is inference, it says so. Two earlier attributions in this investigation
turned out to be wrong and are flagged as such, because the way they failed is
itself useful.

## The finding in one paragraph

On 9.1% of needleleaf-evergreen-temperate ("pine") patches in the 4 km SEUS
runs, and on 78.1% of them in the 0.5 degree runs, that PFT sits at **exactly
zero leaf carbon**, permanently, from early in the spin-up onward. Every
deciduous PFT in the same gridcells is healthy. The gridcell-mean carbon fields
collapse with it, which is what made parts of Georgia and Florida look pale on
the GPP maps that started this. Domain-wide the bias is about 2%; Florida is
11.3% low in GPP and 16.8% low in vegetation carbon, with 38% of its cells
affected.

## What is solid

**It is one PFT class, exactly.** Of the seven PFTs present in this domain, the
two with `evergreen = 1` in `clm_params.nc` die and the five with
`season_decid` or `stress_decid` survive. No exceptions.

| PFT | evergreen | season_decid | stress_decid | outcome |
|---|---|---|---|---|
| needleleaf evergreen temperate | **1** | 0 | 0 | dies |
| broadleaf evergreen shrub | **1** | 0 | 0 | dies |
| broadleaf deciduous temperate tree | 0 | 1 | 0 | survives |
| broadleaf deciduous temperate shrub | 0 | 0 | 1 | survives |
| C3 grass, C4 grass, crop | 0 | 0 | 1 | survives |

**Death is binary, not graded.** At 4 km AD year 201, 9.0% of pine patches are
below LAI 0.01 and 90.9% are above 1.0, with 0.5% in between. At 0.5 degrees,
77.9% below 0.01 and 21.9% above 0.5, nothing between; median pine LAI is
exactly 0.000 while no oak patch is below 0.5.

**It is one-way.** 26 transitions from dead (LAI < 0.5) back to healthy
(LAI > 1.5) across 38 consecutive outputs spanning ~800 model years and 63000
patches. The dead fraction at 4 km is 1.0% at AD year 21, 6.6% at 41, 8.9% at
81, then locked at 9.0-9.1% through 441 years of final spin-up and 174 transient
years.

**The proposed mechanism, from source.**
`CNEvergreenPhenology` in `components/elm/src/biogeochem/PhenologyMod.F90` sets a
background leaf litterfall rate, `lgsf = 0`, and **`bgtr = 0`** - the background
transfer growth rate - and does nothing else. There is no onset event. An
evergreen's leaves come only from current allocation, funded by photosynthesis,
which needs leaves. Drive leafc to near zero and the loop is closed while
background litterfall removes the remainder. `CNSeasonDecidPhenology` and
`CNStressDecidPhenology` are several hundred lines of onset/offset logic that
flush `leafc_storage` into `leafc` each growing season, so a deciduous patch
that loses its canopy gets it back.

The dead patches' numbers are consistent with an absorbing state rather than
slow recovery. At 4 km, final spin-up year 441: LEAFC 0.104 gC/m2, TOTVEGC 1.92,
GPP 3.03e-08, NPP 6.69e-09 - against healthy pine at LEAFC 187, TOTVEGC 12320,
GPP 4.45e-05. NPP is positive but is 0.21 gC/m2/yr, and LEAFC *falls* from 0.148
to 0.104 over those 441 years.

## What was wrong, and why it matters for the review

**Attribution 1, rejected: carbon starvation / respiration squeeze.** An early
pass claimed maintenance respiration ate the photosynthate, citing AR/GPP rising
0.63 to 0.71 with temperature. That statistic was computed as mean(AR)/mean(GPP)
over all patches including dead ones. Among *surviving* pine, per-patch MR/GPP
rises only 0.363 to 0.401 from 10 to 20 C and then flattens at 0.395 and 0.398
in the 20-22 and 22-26 C bands, exactly where 60-70% of patches die. Surviving
pine at 22-26 C has LAI 1.98 and a normal carbon economy. NPP is positive for
100% of the dying cohort before it dies.

**Attribution 2, demoted to "trigger, at 4 km only": fire.** The 4 km AD
spin-up ran with `HDM` (human population density) identically zero for all 201
years, because the CPL_BYPASS HDM reader had its dimensions hardcoded to
720 x 360 against a 504 x 324 SEUS file, `nf90_get_var` failed on the shape
mismatch, and **the return code was written to `ierr` and never checked**. That
is documented at
`ELM_makeSurfdata/Make_surface_data/s8_update_hdm/HDM_high_resolution_cpl_bypass_fix_20260717.md`
and the patch landed 2026-07-17, four days after the AD spin-up ran. In ELM's
fire parameterization population density drives both human ignition and
suppression, so at zero there is no suppression.

The fire evidence at 4 km is real: `COL_FIRE_CLOSS` is 2.95x higher in the dying
cohort pre-mortem, 13.1% of their standing vegetation carbon per year against
2.8%, and binning pine patches by year-21 fire loss gives death rates of 0.1%,
0.4%, 2.8%, 6.2%, 31.0% across quintiles. It survives stratification: within
temperature and sand strata the gradient holds in 7 of 8 strata, and the partial
rank correlation controlling for both is 0.171.

But it cannot be the cause, for two reasons. The oak in the *same* column - fire
is a column-level flux shared by every PFT in it - grew straight through those
fires, LAI 1.78 at year 21 to 2.29 at 201. And the 0.5 degree spin-up reads HDM
correctly (mean 5.066, min 0.0016, max 40.59), has fire two to three orders of
magnitude lower (3e-10 to 2e-8 against ~1e-6), and loses 78.1% of its pine
instead of 9.1%. Less fire, far more death.

**A third suspect, also cleared: `spinup_mortality_factor`.** It is 10 in the
namelist of several cases, but it multiplies only `m_deadstemc_to_litter` and
`m_deadcrootc_to_litter` (and the N/P equivalents) - dead structural pools, not
leaves, not storage - and it is gated on `spinup_state >= 1`. It was inert in
every case except the 4 km AD spin-up, and it applies equally to oak.

## The AD phase amplifies fire three ways, and that is why 4 km burned

`spinup_state == 1` does more than accelerate decomposition. In
`components/elm/src/biogeochem/FireMod.F90`:

```fortran
line 586:  if (spinup_state == 1) fuelc(c) = fuelc(c) + ((spinup_mortality_factor - 1._r8)*deadstemc_col(c))
line 983:  if (spinup_state == 1) m_veg = spinup_mortality_factor
```

So during an AD spin-up the fuel load is inflated by nine times the dead stem
carbon, and **fire-induced vegetation mortality is multiplied by ten**. Stack
that on the 4 km run's zero HDM, which removed the suppression term, and the
result is the ~1e-6 gC/m2/s fire loss measured there against ~1e-8 at 0.5
degrees. The 4 km AD spin-up was burning under three amplifications at once.

This also retires `spinup_mortality_factor` as a red herring: it does not kill
leaves through gap mortality, but it does raise fire kill tenfold, so it matters
after all - just through the fire module, not the mortality module.

## The 0.5 degree trigger: nitrogen limitation, from the missing AD

The 0.5 degree pine never established at all - all 526 patches were below LAI
0.5 at year 21, where 4 km pine was already at 1.55. The cause is visible in the
nutrient diagnostics:

| run | year | FPG | FPI | SMINN | TOTSOMC | HR |
|---|---|---|---|---|---|---|
| 4 km AD | 21 | **1.000** | **1.000** | 0.090 | 459 | 9.4e-06 |
| 0.5 deg | 21 | **0.678** | **0.406** | 0.021 | 118 | 1.5e-06 |
| 0.5 deg | 201 | 0.756 | 0.492 | 0.0020 | 2060 | 5.8e-06 |

With accelerated decomposition on, 4 km has `FPG = 1.000` at year 21 - no
nitrogen downregulation whatsoever, because AD floods the system with mineral N.
Without it, the 0.5 degree run sits at `FPG = 0.678`, growth downregulated by a
third, with four times less mineral N, four times less soil carbon and six times
less heterotrophic respiration. Establishment is slow enough that evergreens
never cross the threshold, while deciduous PFTs, which flush from storage each
spring regardless, do.

So the two resolutions had different triggers, and both trace to configuration:
4 km burned because AD amplified fire while broken HDM removed suppression;
0.5 degrees starved because AD was never switched on. The phenology trap turned
both triggers into permanent holes.

## How the 0.5 degree AD setting was missed

A search of prior session transcripts finds `-bgc_spinup on` in exactly one
place: a July 2026 script for the 4 km chain, as
`./xmlchange --append ELM_BLDNML_OPTS="-bgc_spinup on"`. It appears in neither
of the two sessions that built the 0.5 degree cases on 2026-08-31. Those
sessions do contain the string, but only inside the auto-generated `lnd_in`
comment `! Set spinup_state by the CLM_BLDNML_OPTS -bgc_spinup setting`, which
is boilerplate, not a setting.

The failure mode is that nothing complains. `create_newcase` succeeds, the case
builds, it runs 201 years, it writes files named `ad_spinup`, and only
`spinup_state = 0` deep in `lnd_in` records that it was never an AD spin-up.

## Why the missing AD wrecks the 0.5 degree carbon state, exactly

Not "AD converges faster". The AD pools are deliberately **small** - accelerated
turnover means a smaller steady-state stock - and the whole scheme depends on
ELM multiplying them back up at the handoff. In
`components/elm/src/data_types/ColumnDataType.F90` around line 3056:

```fortran
if (exit_spinup) then
   m = decomp_cascade_con%spinup_factor(k)
   if (decomp_cascade_con%spinup_factor(k) > 1) m = m / cnstate_vars%scalaravg_col(c,j)
else if (enter_spinup) then
   m = 1. / decomp_cascade_con%spinup_factor(k)
```

`exit_spinup` fires when a run with `spinup_state = 0` reads a restart written
with `spinup_state = 1`. **The 0.5 degree restart said 0**, so it never fired.

The handoff numbers show it plainly:

| chain | TOTSOMC at end of "AD" | at start of final spin-up | ratio |
|---|---|---|---|
| 4 km | 697 | 15320 | **22x** |
| 0.5 deg | 2060 | 2173 | 1.05x |

So the 0.5 degree final spin-up began from a soil carbon state roughly seven
times too low and spent 441 years crawling up from far below, ending at 6752
against 4 km's 16960, still drifting 13.0% per century against 4 km's 0.8%.

Note the tell: the 0.5 degree "AD" ended *higher* than the 4 km AD (2060 vs
697), which looks healthier and is exactly backwards. An AD spin-up that ends
with more soil carbon than a real one is a sign it was never accelerated.

## Should fire be off during AD? No - the reference case has it on

`20260519_Southeast_hires_ICB1850CNRDCTCBC_ad_spinup`, taken as the known-good
configuration, has:

- `ELM_BLDNML_OPTS ... -bgc_spinup on`, `spinup_state = 1`
- `nyears_ad_carbon_only = 25`, `spinup_mortality_factor = 10` (both defaults)
- **no `use_nofire`** - fire is on
- `stream_fldfilename_popdens = .../elmforc.Li_20181205_mod_hist_SSP2_CMIP6_hdm_0.5x0.5_AVHRR_simyr1850-2100_c240906.nc`

That last line is the whole story. The standard global population file is
**720 x 360** - exactly the dimensions the old CPL_BYPASS reader had hardcoded.
It worked. The reader only broke when the project switched to the custom
high-resolution SEUS file `elmforc.Li_hdm_1_24x1_24_bilinear_SEUS_simyr1850-2100.nc`
at 504 x 324 for the 2026-07-12 run, and the unchecked `nf90_get_var` return
code turned that into a silent zero.

So the correct fix for 4 km is not to disable fire in AD. It is to run AD with
fire on and HDM actually read - which is exactly what job 522373 is doing. That
restores the reference configuration rather than departing from it, and it makes
the experiment a direct test rather than the half-test described below.

## Open questions for the reviewer

1. **Is the phenology reading right?** Specifically: is there any pathway by
   which an ELM evergreen patch at `leafc ~ 0` with `leafc_storage ~ 0` can
   rebuild a canopy, other than a `dwt_` seed flux from a land-cover-change
   transition? If there is, the absorbing-state explanation is wrong.

2. **Is this a known E3SM/CLM issue?** A cold-start AD spin-up stranding an
   arbitrary fraction of evergreen PFTs at zero seems too general to be
   specific to this domain, yet it is not something we have seen written down.

3. **Why does the 0.5 degree transient repair it and the 4 km one not?** Pine
   at 0.5 degrees goes from 78.1% dead at the end of spin-up to 9.9% dead by
   2023, coinciding with land-cover-driven PFT weight changes (pine's weight
   share 40.9% to 30.1%, C4 grass from 1 patch to 130). The seed-carbon pathway
   is the obvious candidate but has not been verified in the output.

4. **How much of the 0.5 degree chain has to be redone?** Its `ad_spinup` was
   not an AD spin-up (`spinup_state = 0`, no `-bgc_spinup on`), so 201 years
   meant to accelerate decomposition ran at normal rates. Soil carbon there was
   still climbing steeply at year 201 (118 to 2060 gC/m2 over the run, against
   4 km reaching 459 by year 21), so the whole chain may be far from
   equilibrium, not just the evergreens. That is a separate and possibly larger
   problem than the dieback.

   For the record, the 4 km final spin-up
   (`/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC`)
   is **correctly** configured: `spinup_state = 0`, so its leftover
   `spinup_mortality_factor = 10` and `nyears_ad_carbon_only = 25` are inert.

## Experiment in flight

Job **522372**, submitted 2026-09-09, 12 nodes on the `hpcl-cli185` partition
and QoS, about 11 hours for 80 model years.

`20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup` is a
clone of the original 4 km AD spin-up, identical in every input, PE layout and
namelist, differing only in that its E3SM source reads HDM correctly. RUNDIR and
EXEROOT on scratch under the same case name.

It tests whether the 4 km AD spin-up run as intended - fire on, AD fuel and
mortality amplification on, HDM actually read so suppression works - keeps its
pine. That is the reference configuration of
`20260519_Southeast_hires_ICB1850CNRDCTCBC_ad_spinup`, so this is a direct test
of whether the HDM breakage alone accounts for the 4 km dieback, not a
departure from the intended setup.

First submission (522372) failed in 22 seconds on `GETFIL: FAILED to get
/domain.nc`. `ATM_DOMAIN_PATH` and `LND_DOMAIN_PATH` are empty in this case
lineage and `ATM_DOMAIN_FILE` is the bare name `domain.nc`, which GETFIL
resolves against RUNDIR; the original case had a real `domain.nc` staged in its
run directory and the fresh scratch RUNDIR did not. Symlinking it across fixed
it. Job **522373** is the live one. `compare_ad_hdm_test.py` in this
directory produces the verdict table: HDM (zero would void the experiment), fire
loss, pine dead fraction against the control's 1.0 / 6.6 / 7.8 / 8.9%, and
`NDEP_TO_SMINN` as a confound check, since the source tree also gained a Ndep
calendar-year fix between the two runs.

## Interim result from job 522373: fixing HDM rescues most of the pine

Two comparable checkpoints so far, control against experiment:

| year | HDM | fire loss gC/m2/s | **pine dead %** | NDEP_TO_SMINN |
|---|---|---|---|---|
| 21 | 0.000 / **5.128** | 1.17e-06 / 3.43e-07 | 1.0% / **0.4%** | 1.99e-08 / 1.98e-08 |
| 41 | 0.000 / **5.128** | 1.02e-06 / 3.52e-07 | **6.6% / 0.9%** | 1.99e-08 / 1.98e-08 |

HDM now reads 5.128, matching the final spin-up. Fire drops to about a third.
The dead fraction goes from 6.6% to 0.9% at year 41. At patch level, of the
4556 pine patches the control has killed by then, **87.8% are alive in the
experiment**, at mean LAI 1.468 against 1.831 for pine that never came close to
dying.

`NDEP_TO_SMINN` is 1.99e-08 against 1.98e-08, so the Ndep calendar-year fix that
also landed between the two source versions is a no-op for this configuration.
The experiment isolates HDM cleanly.

**This converts fire from an inferred trigger to a demonstrated one, at 4 km.**
Only HDM changed; fire fell; the pine lived. It also says a rerun of the 4 km
chain with the corrected reader would largely work.

Three caveats. The run is only at year 41 of 80 - the control kept climbing to
8.9% by year 81 and 9.1% by 201, so the experiment may lose more, though the
trajectories differ sharply already (1.0 to 6.6% against 0.4 to 0.9%). The fix
is not complete: 0.9% still die, consistent with fire still being amplified by
the AD fuel and mortality factors even with suppression restored. And none of
this removes the phenology trap - it only removes a trigger strong enough to
push patches into it.

## How to reproduce any of this

Everything comes from the `h1` PFT-vector history files (`hist_dov2xy = .false.`),
which exist for both spin-ups and the transient at both resolutions. A
50-variable screen of gridcell-mean `h0` fields found nothing; one `h1` read made
the cause obvious. When a gridcell-average field looks inexplicably low, go to
`h1` first.

Three traps cost time here. The AD year-0001 `h1` file is the cold start with
LAI 0 everywhere, so it must be excluded from any "first year dead" test.
`PCT_CROP` and `PCT_NATVEG` in the landuse timeseries file are static 2-D fields,
not time-varying, so indexing them by a time step silently broadcasts one
latitude row. And `netCDF4` applies `scale_factor` itself, so applying it again
to the cpl_bypass forcing silently scales precipitation by 2.7e-06.
