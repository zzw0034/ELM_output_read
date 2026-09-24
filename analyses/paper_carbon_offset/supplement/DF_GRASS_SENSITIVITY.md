# Does ELM's over-productive grass bias the avoided-deforestation offset?

## Current status — 2026-09-22

The September 15 assessment below is a historical investigation. Newer
[daylength-threshold diagnostics](../../CRIT_DAYL_STRESS_ARTIFACT.md) document
the parameter-driven discontinuity near 30.833°N under
`crit_dayl_stress=36000 s`, in both 0.5° and 4 km outputs. Source/parameter
checks, seasonal and PFT contrasts, and paired sensitivity reruns now provide
evidence beyond this folder's original domain-mean BTRAN/TLAI screening.

The September 22 record reports four-SSP, 0.5° future reruns with both Default
and DF at 38000 s. The threshold discontinuity in their difference is much
reduced; cumulative NBP avoided-loss benefits for 2024–2100 increase by
5.3–5.9%, and the 2100 end-state TOTECOSYSC differences by about 5.0–5.7%.
These are reported results from the linked analysis, not recomputed here.
They must not be applied as a correction factor to the old 2091–2100 mean
stock-benefit table.

This moves the issue from an untested mechanism to a documented parameter
sensitivity. It does not establish a bias relative to reality: 38000 s also
imposes stronger southern winter dormancy, and the starting restart was spun
up under 36000 s. Changing only DF leaves Default's threshold structure in
the difference. The actual rerun implementation is in
`../20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000/`.

For the high-resolution manuscript, test how this artifact affects observed
spatial skill, within-cell heterogeneity, and priority-area rankings. Do not
count a sharper artificial boundary as a resolution advantage, or describe
the original grass-SOC bias as proven conservative. Verify case membership
before extrapolating these 0.5° Default/DF results to RF/RH or 4 km.

## Historical investigation — 2026-09-15

The sections below preserve the earlier evidence and correction history.
Their “not checked”, “no rerun” and proposed-manuscript language describe
September 15 only; use the current status above for present-day writing.

**Status (2026-09-15, revised after Codex independent review):** this is a
**well-supported hypothesis with a plausible mechanism, not a completed,
validated sensitivity analysis.** The 2026-09-14 version of this document
overstated what had actually been checked -- several specific overclaims are
corrected below. The direction of the likely bias (conservative) is now
**uncertain**, not confirmed, because the literature claim it rested on was
wrong (see Step 3). No rerun has been done; whether one is needed is now an
open question, not a closed one.

## The concern

The DF (deforestation counterfactual) run converts all forest to grass.
`Default − DF` is the paper's avoided-deforestation offset (proposal
Table 2). Earlier analysis of this case family found that ELM's grass and
shrub PFTs in SEUS have *higher* per-area GPP than deciduous broadleaf
forest, which looks backwards. If grass productivity is overstated, the DF
run retains too much carbon, and `Default − DF` could be biased.

Because that difference *is* the headline number of the manuscript, this
needed to be checked before the result could be used with confidence.

## Step 1 — decompose the offset into a less-sensitive term and a more-sensitive term

`Default − DF` splits into a vegetation-carbon term and a
soil+litter+CWD term.

**Correction (2026-09-15):** the earlier version of this document called the
vegetation term "insensitive to grass productivity errors" because it's
"driven by trees having woody stems, grass not having them." That is too
strong. The vegetation term is `TOTVEGC`, which for grass PFTs **includes**
grass's own leaf and root biomass, not just the tree-vs-grass structural
difference — so it is not fully insulated from a grass-GPP bias, only less
exposed to it than the litter/soil term (which is fed directly by litter
inputs).

Script: `check_df_grass_decomposition.py`. **0.5° SSP3-7.0 result:**

| year | total (PgC) | vegetation | soil+litter+CWD | vegetation share |
|---|---:|---:|---:|---:|
| 2024 | 6.073 | 10.694 | −2.015 | 176% |
| 2050 | 8.869 | 7.446 | +1.209 | 84.0% |
| 2075 | 9.708 | 7.840 | +1.350 | 80.8% |
| 2100 | 9.971 | 8.049 | +1.314 | 80.7% |

2091-2100 mean: **total 9.883 PgC, vegetation 7.931 (80.2%),
soil+litter+CWD 1.335 (13.5%)**, remainder ~6% not covered by the four
summed terms (this decomposition itself does not fully close -- the 6%
residual has not been chased down; see the caveat in `fig03`'s docstring).

**What this does and doesn't show**: ~80% of the offset sits in a term that
is *less* exposed to a grass-GPP bias (dominated by tree woody biomass, but
not purely so). This is evidence the headline number is not *maximally*
sensitive to the grass issue, not proof that it is *insensitive*. A bias in
grass's own vegetation carbon (leaf/root growth, not just wood) would still
flow through this 80% term to some degree.

The 2024 row is not an artefact: DF clears forest instantaneously in 2024,
so that year's felled biomass is sitting in the litter/CWD pools and DF
momentarily holds *more* dead carbon than Default (hence the negative dead
term and >100% vegetation share). By 2050 that debris has decomposed and the
term flips positive. This transient is visible in fig01's middle panel and
is worth one sentence in the Results.

## Step 2 — a candidate mechanism (why grass might not go dormant) -- NOT a paired validation

Script: `check_grass_phenology_mechanism.py`. Monthly PFT-level BTRAN
(soil-water stress factor; 1 = unstressed) and TLAI, 0.5° SSP3-7.0, 2100
(numbers below re-run 2026-09-15 after fixing a PFT-weighting bug -- see
"Bug fixed" below; the fix changed nothing materially):

| PFT | phenology | min BTRAN | min TLAI |
|---|---|---:|---:|
| BDT_temp (deciduous broadleaf tree) | `season_decid` | 0.83 | **0.00** |
| C3_grass | `stress_decid` | 0.89 | 2.30 |
| C4_grass | `stress_decid` | 0.87 | 1.44 |
| BDS_temp (shrub) | `stress_decid` | 0.93 | 3.61 |
| crop_unmanaged | `stress_decid` | 0.84 | 1.42 |

**What this shows**: BDT_temp and C3_grass experience similar *domain-mean
monthly* water status (min BTRAN 0.83 vs 0.89), yet BDT_temp goes to exactly
zero LAI for three months while grass never drops below ~20-40% of its peak.
Leaf-level photosynthetic parameters are identical between them (`slatop`
0.03, `leafcn` 25, `fnitr` 1.0 — standard CLM5 values, verified in
`clm_params.nc`).

**What this does NOT show, corrected 2026-09-15 (Codex review)**:

1. This checks **SSP3-7.0 Default's** grass/shrub PFTs, not the actual grid
   cells DF converts from forest to grass. Forest and grass are not
   co-located in Default (different places, different local climate) — this
   is not a paired same-site comparison of "this forest cell" vs "what it
   becomes in DF".
2. It is a **domain-average, monthly** statistic. A regional-mean BTRAN that
   stays near 1 does not rule out individual gridcells, or sub-monthly
   periods, crossing the stress threshold.
3. `tc_stress` (cold-stress trigger) and `crit_dayl_stress` (day-length
   stress trigger) are documented parameters but **were never actually read
   or checked** — only BTRAN (water stress) was examined. Calling the
   mechanism "purely water-driven, not day-length-controlled" was not
   something this script verified.
4. Identical leaf parameters do not by themselves prove the *entire* annual
   GPP gap is explained by growing-season length; other pathways (N/P
   limitation, allocation, fire-driven differences) were not excluded.

**Corrected framing**: the simulation shows a real, substantial difference
in how long forest vs. herbaceous PFTs keep green leaf area through winter,
and day-length-vs-stress-triggered phenology is a plausible, mechanistically
sound *candidate* explanation. It has not been validated against paired
sites, sub-monthly data, or the temperature/day-length triggers specifically.
Real-world southeastern warm-season grasses do senesce in winter under low
temperature and photoperiod — if ELM's stress-deciduous formulation for
these PFTs does not represent that trigger, that would explain the pattern,
but this has not been confirmed against the actual trigger variables.

### Bug fixed 2026-09-15 (Codex review): PFT weighting

`check_grass_phenology_mechanism.py` and `common.py`'s `load_pft_type_series`
(used across this analysis, including the earlier spinup/transient PFT-level
figures in the sibling case-family folders) weighted by `pfts1d_wtgcell`
alone — a dimensionless fraction of the gridcell — without multiplying by
the gridcell's physical area. Gridcells at different latitudes have
different physical size (this domain spans 24-37°N, ~14% area variation),
so this gave gridcells implicit equal weight regardless of size — the same
class of error as the project's `weighted_vs_unweighted_spatial_means_qa`
lesson, just applied at the PFT level. **Fixed** in both sibling folders'
`common.py` and in this script (now multiplies by the gridcell's `area`
via `pfts1d_ixy`/`pfts1d_jxy`). Re-running after the fix changed the BTRAN/
TLAI table above by <0.05 in every entry — the qualitative finding is
unaffected for this domain, but the bug was real and any earlier PFT-level
number from before this fix should be treated as approximate.

## Step 3 — direction of the soil-carbon response: RETRACTED claim, corrected

From `check_df_grass_decomposition.py`, DF minus Default soil carbon:
2024 −0.010, 2050 −0.049, **2100 +0.321 PgC**, trend **+0.62 PgC/century**
(model result, not in question).

**The 2026-09-14 version of this document said**: "Real-world forest→pasture
conversion typically *loses* 20-30% of surface SOC. The model's opposite
sign is consistent with the over-productive grass," and concluded this makes
the offset *conservative*.

**This is retracted (Codex review, 2026-09-15).** Guo & Gifford's (2002)
meta-analysis of land-use-change effects on soil carbon reports the average
SOC response to **native forest → pasture** conversion as **+8%** (not a
20-30% loss) — see
[the paper](https://onlinelibrary.wiley.com/doi/10.1046/j.1354-1013.2002.00486.x),
with substantial heterogeneity by region and method. A positive SOC response
to forest→pasture conversion is therefore not obviously unphysical in the
literature; the 20-30%-loss figure this document cited does not appear to be
the right benchmark (its original source was not re-verified and should be
treated as wrong until shown otherwise).

**Consequence**: with the "must be a loss" prior removed, the model's
positive DF-minus-Default SOC response is **no longer evidence of a bias in
a known direction**. It could be within the range of real-world variability,
or still be biased (in either direction) for reasons unrelated to the
20-30% figure. **The "this makes our estimate conservative" conclusion is
withdrawn.** The direction of any SOC-pathway bias in the avoided-
deforestation offset is currently **unknown**, not "known and safe."

## Step 4 — sensitivity rerun: deferred, not "proven unnecessary"

**Correction (2026-09-15)**: the 2026-09-14 version of this document said a
rerun was "NOT needed" because steps 1-3 showed the bias was small and
conservative. Step 3's conservative-direction claim is retracted (above),
and step 1/2's "insensitive"/"validated mechanism" framing was overstated
(above). The actual basis for skipping a rerun is now only: **the
vegetation-carbon term (which is somewhat, not fully, insulated from the
grass issue) is ~80% of the offset**, so a large error in the sensitive
term would move the headline number by a bounded, probably modest, amount
-- not that the issue has been shown to be small AND safe-direction.

**Honest status: deferred due to resource cost, not resolved.** If this
uncertainty turns out to matter for the paper's central claim, the correct
next step (per Codex) is zonal/monthly diagnostics on the actual DF
conversion gridcells specifically (paired forest-vs-post-conversion-grass
comparison, checking `tc_stress`/`crit_dayl_stress` triggers directly, not
just BTRAN), before considering a rerun with modified grass phenology.

## What to say in the manuscript (revised, hedged)

For the Methods/model-limitations paragraph:

> In ELM, the herbaceous and shrub plant functional types are
> stress-deciduous, dropping foliage in response to soil-water or
> cold-temperature stress, whereas temperate deciduous broadleaf trees are
> day-length-deciduous. Domain-mean monthly water stress (BTRAN) is similar
> between these types in our simulations, yet simulated grasses retain
> 20-40% of peak leaf area through winter while deciduous forest is fully
> dormant for three to four months. This is consistent with — but has not
> been directly validated against — the stress-deciduous formulation failing
> to represent the temperature/photoperiod-driven winter senescence observed
> in real southeastern warm-season grasses. We did not verify this against
> the model's own day-length or cold-stress trigger variables, nor against
> paired forest/grassland sites.

For the Discussion/limitations, on what it means for the offset estimate:

> Because the deforestation counterfactual replaces forest with grass, and
> simulated grass in this region appears to have an extended effective
> growing season relative to deciduous forest, the possibility of a bias in
> the avoided-deforestation offset cannot be ruled out. Decomposing the
> estimate shows ~80% derives from the vegetation-carbon difference (which
> includes but is not limited to woody biomass) and is therefore only
> partially insulated from this issue. We do not have a validated estimate
> of the bias's sign or magnitude: an earlier assumption that observed
> forest-to-pasture soil carbon loss constrains the direction does not hold,
> since the relevant meta-analysis (Guo & Gifford, 2002) reports a small
> **positive** average SOC response to native forest→pasture conversion, not
> a loss. We flag this as an open uncertainty for future work rather than a
> quantified, signed correction.

## Reproduce

```bash
# Historical screening scripts; remote execution requires approved Slurm jobs.
sbatch --export=NONE -J dfdecomp05 code/submit_py.sbatch code/check_df_grass_decomposition.py 0.5deg
sbatch --export=NONE -J grass05 code/submit_py.sbatch code/check_grass_phenology_mechanism.py 2100 0.5deg

# 4 km must go through Slurm on the dedicated partition
sbatch --export=NONE -J dfdecomp4km code/submit_py.sbatch code/check_df_grass_decomposition.py 4km
```
