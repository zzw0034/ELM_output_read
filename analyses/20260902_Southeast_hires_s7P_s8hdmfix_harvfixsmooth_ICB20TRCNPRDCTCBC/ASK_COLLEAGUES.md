# Question for colleagues: have you seen evergreen PFTs die out during ELM spin-up?

## The short version

In our ELM offline runs over a custom Southeast US grid, the evergreen PFTs go
to **exactly zero leaf carbon on a fraction of their patches during the AD
spin-up and never come back**. Deciduous PFTs in the same gridcells are
completely unaffected. We would like to know whether this is familiar to anyone,
and whether there is a standard guard against it.

## What we see

Two independent chains, both cold-started, both AD spin-up then final spin-up
then 1850-2023 transient:

| | 4 km chain | 0.5 degree chain |
|---|---|---|
| needleleaf evergreen temperate patches at zero | **9.1%** | **78.1%** |
| broadleaf evergreen shrub | collapsed | 100% |
| every deciduous PFT | unaffected | unaffected |

The distribution is **binary, not graded**. At 4 km, AD year 201: 9.0% of pine
patches below LAI 0.01, 90.9% above 1.0, 0.5% in between. At 0.5 degrees: 77.9%
below 0.01, the rest healthy, nothing between, median exactly 0.000 - while not
one oak patch is below LAI 0.5.

It is **one-way**. 26 transitions from dead (LAI < 0.5) back to healthy
(LAI > 1.5) across 38 consecutive history outputs spanning ~800 model years and
63,000 patches. At 4 km the dead fraction is 1.0% at AD year 21, 6.6% at 41,
8.9% at 81, then locked at 9.0-9.1% through 441 years of final spin-up and all
174 transient years.

A dead patch is genuinely dead, not merely thin. At the end of the final
spin-up: LEAFC 0.104 gC/m2, TOTVEGC 1.92, GPP 3.03e-08 gC/m2/s, against healthy
pine in the same run at LEAFC 187, TOTVEGC 12320, GPP 4.45e-05. Its NPP is
positive but is 0.21 gC/m2/yr, and its LEAFC *declines* over those 441 years.

The PFT selectivity is exact. Of the seven PFTs present in our domain, the two
with `evergreen = 1` in `clm_params.nc` die and the five with `season_decid` or
`stress_decid` survive. No exceptions.

## Our reading of the mechanism, which we would like checked

`CNEvergreenPhenology` in `components/elm/src/biogeochem/PhenologyMod.F90` sets
a background leaf litterfall rate, `lgsf = 0`, and **`bgtr = 0`**, and nothing
else. There is no onset event. An evergreen's leaves come only from current
allocation, which photosynthesis funds, which requires leaves. Drive leafc to
near zero and the loop is closed, while `bglfr_leaf = 1/leaf_long` keeps
removing the remainder.

`CNSeasonDecidPhenology` and `CNStressDecidPhenology` are several hundred lines
of onset/offset logic that flush `leafc_storage` into `leafc` each growing
season, so a deciduous patch that loses its canopy gets it back next spring.

If that reading is right, zero leaf carbon is an absorbing state for evergreens
and only for evergreens, and any transient knock during establishment from bare
ground is enough to strand a patch there permanently.

## The triggers we found, which differ between the two chains

Neither is the interesting part - the trap is - but for completeness:

- **4 km**: fire. Its AD spin-up ran with human population density identically
  zero, because the CPL_BYPASS HDM reader had dimensions hardcoded to 720x360
  and our custom file is 504x324, with the `nf90_get_var` return code never
  checked. That removed the suppression term. On top of that, `spinup_state==1`
  inflates the fuel load by `(spinup_mortality_factor-1)*deadstemc`
  (`FireMod.F90:586`) and multiplies fire-induced vegetation mortality by
  `spinup_mortality_factor` (`FireMod.F90:983`). Fire loss there was ~1e-6
  gC/m2/s; the dying cohort burned 13.1% of standing vegetation carbon per year
  against 2.8% for survivors, and death rate rises 0.1% to 31.0% across fire
  quintiles.
- **0.5 degree**: nitrogen limitation. That case was accidentally built without
  `-bgc_spinup on`, so it ran with `spinup_state = 0` and no acceleration.
  `FPG` is 0.678 at year 21 there against exactly 1.000 in the 4 km AD, with
  four times less mineral N. Establishment was slow enough that the evergreens
  never crossed the threshold. Fire there was ~1e-8, two to three orders of
  magnitude below 4 km, and it still lost eight times as much pine.

## What we are asking

1. Have you seen evergreen PFTs strand at zero leaf carbon during a cold-start
   spin-up, at any resolution or domain?
2. Is our reading of `CNEvergreenPhenology` correct - is there genuinely no
   pathway for an evergreen patch at `leafc ~ 0` and `leafc_storage ~ 0` to
   rebuild a canopy, other than a `dwt_` seed flux from a land-cover-change
   transition?
3. If it is a known behaviour, is there a recommended guard? Initializing from
   an existing spun-up state rather than bare ground, a minimum leaf carbon
   floor, `use_nofire` during AD, or something else?
4. Does anyone routinely check per-PFT LAI after spin-up? Our gridcell-mean
   fields looked merely low, not obviously wrong; it took reading the
   PFT-vector `h1` output to see that one PFT was simply absent.

## Why it matters to us

Domain-wide the carbon bias is about 2%, but it is concentrated: over Florida,
38% of land cells are affected, GPP is 11.3% low and vegetation carbon 16.8%
low. Real Southeast US flatwoods are pine-dominated and our run says they are
not. Everything downstream - the historical run and the future scenarios -
inherits the hole.
