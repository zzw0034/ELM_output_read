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

4. **A separate misconfiguration, found while checking the above.** The 0.5
   degree case named `20260831_seus_halfdeg_ad_spinup` has `spinup_state = 0`
   and no `-bgc_spinup on` in `ELM_BLDNML_OPTS`. It is not an
   accelerated-decomposition spin-up despite the name. The 4 km AD spin-up has
   `spinup_state = 1` and `-bgc_spinup on` as expected. This needs its own
   assessment: 201 years of intended AD may have done far less spin-up work than
   planned, which could be why the 0.5 degree vegetation is so much further from
   equilibrium.

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

It tests whether removing the fire trigger saves the pine at 4 km. Given the 0.5
degree result the expected answer is no, in which case both fire and HDM are
closed out and the phenology trap stands alone. `compare_ad_hdm_test.py` in this
directory produces the verdict table: HDM (zero would void the experiment), fire
loss, pine dead fraction against the control's 1.0 / 6.6 / 7.8 / 8.9%, and
`NDEP_TO_SMINN` as a confound check, since the source tree also gained a Ndep
calendar-year fix between the two runs.

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
