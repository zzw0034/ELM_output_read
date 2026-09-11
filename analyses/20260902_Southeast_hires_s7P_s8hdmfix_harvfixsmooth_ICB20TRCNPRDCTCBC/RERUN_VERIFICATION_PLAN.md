# 4 km rerun: verification plan for the combined HDM + coastal-mapping fixes

Companion to [EVERGREEN_DIEBACK.md](EVERGREEN_DIEBACK.md), which is the
investigation record. This file is the forward-looking plan: what to run, what
to output, what to measure, and what result permits moving on.

Written 2026-09-10. Every fact marked **measured** was read from a case
directory, a job record, a model output file or the E3SM source on that date.
Everything else is labelled as expectation or inference.

## 0. Three verification goals, deliberately kept apart

The single biggest risk in this rerun is collapsing three different questions
into one "did it get better" number. They are separated everywhere below.

| goal | question | evidence type | can fail independently |
|---|---|---|---|
| **G1 inputs corrected** | does the model now read the intended HDM and the intended met forcing at every land cell? | static, input-side, no vegetation involved | yes |
| **G2 vegetation state improved** | do the evergreen PFTs now establish and stay established, by PFT and by region? | model output, per-PFT, per-window | yes |
| **G3 residual mechanism identified** | what actually removes leaf carbon from the 405 south-Florida pine patches? | annual per-patch leaf carbon budget | yes |

G1 is a precondition for any statement about G2. G2 can pass while G3 stays
open, and that is an acceptable outcome to proceed on, provided the residual
population is small, bounded and flat over time. G3 failing while G2 passes is
a documentation problem, not a blocker. G1 failing is always a blocker.

---

## 1. What the existing jobs already establish

### 1.1 Job 522626 — annual AD diagnostic (**measured**)

`20260910_ADdiag_annual_ICB1850CNRDCTCBC_ad_spinup`.

| property | value | source |
|---|---|---|
| state | COMPLETED 2026-09-10 18:35:54, 02:17:54 elapsed | `sacct -j 522626` |
| nodes | 20, `blc[081-093,095-101]` | `squeue` while running |
| model years | 30 (`STOP_N=30`, `STOP_OPTION=nyears`, `RUN_STARTDATE=1-01-01`) | `xmlquery` |
| output | `hist_nhtfrq = -8760,-8760`, `hist_mfilt = 30,30`, `hist_dov2xy = .true.,.false.` | `CaseDocs/lnd_in` |
| AD settings | `spinup_state = 1`, `nyears_ad_carbon_only = 25`, `spinup_mortality_factor = 10`, `suplnitro='NONE'`, `suplphos='ALL'`, `nu_com='RD'` | `CaseDocs/lnd_in` |
| executable | `EXEROOT` points at the **2026-07-12** build | `xmlquery EXEROOT` |
| forcing | `metdata_bypass = .../Daymet_ERA5_TESSFA2/cpl_bypass_full` | `CaseDocs/lnd_in` |

Two properties of that configuration matter more than the rest.

**It runs the pre-fix HDM executable.** The build is dated 2026-07-12 and the
HDM reader patch landed 2026-07-17, so this run still has human population
density identically zero. Fire is unsuppressed, exactly as in the original AD
spin-up. That is intentional: it is a diagnostic of the collapse, not of the
repair.

**It is the first run to read the corrected `zone_mappings.txt`.** The five
mapping tables were rewritten between 15:24 and 15:44 on 2026-09-10; the job
started at 16:18. File times and sizes, **measured**:

| table | mtime | lines | original lines |
|---|---|---|---|
| `cpl_bypass_full` | 15:24 | 117,964 | 225,625 |
| `future_clim/ssp119` | 15:29 | 117,964 | 225,625 |
| `future_clim/ssp245` | 15:34 | 117,964 | 225,625 |
| `future_clim/ssp370` | 15:39 | 117,964 | 225,625 |
| `future_clim/ssp585` | 15:44 | 117,964 | 225,625 |

So job 522626 carries a free, already-paid-for test of the coastal fix in a
real model run, which until now had only the static nearest-neighbour replay
behind it. Nothing has been read out of its output yet — see section 6.

**What it can answer.**

1. **G1, coastal half.** Its `h0` tape carries `TBOT`, `FSDS` and `GPP` on the
   gridded mesh, annually. The 194 previously-affected land cells either read
   physical forcing now or they do not. This is a direct measurement in the
   model's own reader, not a replay of the selection logic.
2. **Collapse timing without the 20-year smear.** Section 6 of the dieback
   record retracts every timing statement because the production tapes are
   20-year means. This run is annual for 30 years, which brackets the window
   where most of the collapse happens.
3. **A partial leaf budget.** It carries `LEAFC`, `LEAFC_ALLOC`, `LEAFC_LOSS`
   and `LEAFC_TO_LITTER`, so `LEAFC_LOSS - LEAFC_TO_LITTER` gives total
   non-litterfall leaf loss as one lumped term.
4. **XR is recoverable by arithmetic.** `VegetationDataType.F90:8256` sets
   `ar = mr + gr + xr` for the non-crop `nu_com='RD'` branch, so
   `XR = AR - MR - GR` exactly, from fields the run already has.
   This closes only the **availability** half of the dieback record's XR item.
   The mechanism half stays open: it still requires reading the data and
   establishing XR's magnitude before and after the decline, and its relation
   to `CPOOL` and temperature. Recovering a flux is not explaining it.

**What it cannot do.**

- It cannot split fire from background mortality, because
  `M_LEAFC_TO_FIRE`, `M_LEAFC_TO_LITTER_FIRE` and `M_LEAFC_TO_LITTER` are all
  registered `default='inactive'` and are absent from its `hist_fincl`.
  This is precisely the term G3 needs.
- It cannot say anything about the combined fix. With HDM at zero the
  domain-wide fire trigger is still active, so its stranded fractions are
  control values, not repaired ones.
- 30 years stops inside the collapse, not after it. From the 522373 windows the
  405 residual patches go 107 → 382 → 395 → 405 below threshold across windows
  1-20, 21-40, 41-60, 61-80. Year 30 is mid-transition.
- It is not the production configuration and must not be presented as one.

### 1.2 Job 522677 — matched fire analysis of the 405 (**measured**)

Read out of `outputs/residual_pine_fire_522677/summary.json`. Means over each
20-year window; `fire_gC_m2_yr` is column fire loss, not pine leaf fire loss.

| window | 405 TLAI | 405 LEAFC | 405 fire | matched control fire | ratio | 405 below threshold |
|---|---|---|---|---|---|---|
| 1-20 | 0.940 | 89.6 | 95.1 | 23.2 | 4.10 | 107 |
| 21-40 | 0.162 | 15.7 | 109.3 | 25.5 | 4.29 | 382 |
| 41-60 | 0.027 | 2.6 | 53.6 | 20.4 | 2.62 | 395 |
| 61-80 | 0.015 | 1.4 | 69.4 | 33.6 | 2.07 | 405 |

Three things follow that sharpen the plan, none of which prove causation.

**The fire excess is largest before the collapse, not after.** The 4.1x ratio
in window 1-20 is carried while the patches still hold 59% of the control's
leaf carbon. The ratio then falls as the patches empty. A consequence-of-death
artifact would run the other way.

**Nitrogen is not the initiator for this group.** `FPG` is exactly 1.000 for
both target and control in window 1-20, because that window lies entirely
inside `nyears_ad_carbon_only = 25`. The divergence (0.913 against 0.946)
appears only in window 21-40. But window 21-40 also contains the collapse, so
within-window ordering is unresolved at this output frequency.

**The collapse concentrates in years 21-40.** 107 → 382 in one window.

**None of this yet excludes the two standing alternatives.** An early fire
excess of 4.1x strengthens the fire hypothesis but does not rule out a common
environmental driver that raises both fire and mortality, and 20-year means
cannot order events inside a window in any case. Nor does `FPG = 1.000` in
window 1-20 clear nitrogen: it rules out nitrogen downregulation **in that
window only**, because that window lies inside the carbon-only phase. Nitrogen
limitation resuming at year 26 can still participate in widening the decline
through windows 21-40 and later. Both alternatives are tested on the annual
axis, not on these windows.

### 1.3 Source facts verified for this plan (**measured**, from `SRCROOT`)

`SRCROOT = /projects/hpcl-cli185/proj-shared/zw5/E3SM`.

**The leaf carbon budget closes exactly, with named fields.**
`VegetationDataType.F90:8410-8428`:

```fortran
leafc_alloc(p) = leafc_xfer_to_leafc(p) + cpool_to_leafc(p)

leafc_loss(p)  = m_leafc_to_litter(p)      &
               + m_leafc_to_fire(p)        &
               + m_leafc_to_litter_fire(p) &
               + leafc_to_litter(p)        &
               + hrv_leafc_to_litter(p)
```

So `d(LEAFC)/dt = LEAFC_ALLOC - LEAFC_LOSS` holds as a **flux identity at the
model time step**, and `LEAFC_LOSS` decomposes into background mortality, fire
combustion, fire mortality to litter, litterfall and harvest.
`hrv_leafc_to_litter` has **no history field registered**, checked; it appears
only as a pointer and in the sums. In this AD compset there is no
`flanduse_timeseries` and no `do_harvest` in `lnd_in`, so it should be zero.

**That identity does not by itself make an annual state budget checkable.** The
history tapes carry `avgflag='A'`, so an annual `LEAFC` record is the mean of
the year, not the state at either end of it. The difference between two annual
means is not the year's change in leaf carbon, and comparing it against the
year's integrated fluxes folds a lag into the residual. A strict check needs
**end-of-year state**: leaf carbon at the year boundary minus leaf carbon at
the previous year boundary, against the time integral of allocation and loss
between them.

Two further reasons a residual cannot be read as one missing term.
`PrecisionControlMod` truncates very small leaf carbon to zero, which removes
carbon without any flux recording it, and that truncation is most active
exactly in the collapsing patches this analysis targets. And any transfer
outside the five named terms, for instance a patch-weight change, also lands in
the residual. A non-zero residual is a signal to look, not evidence of
harvest.

**Fire leaf loss is not multiplied by `spinup_mortality_factor`.**
`FireMod.F90:1012` and `FireMod.F90:1083`:

```fortran
m_leafc_to_fire(p)        = leafc(p) * f * cc_leaf(itype)
m_leafc_to_litter_fire(p) = leafc(p) * f * (1 - cc_leaf(itype)) * fm_leaf(itype)
```

`m_veg = spinup_mortality_factor` multiplies only dead stem and dead coarse
root terms. The AD amplification reaches leaves indirectly, through `fuelc` and
therefore `farea_burned`. This refines item 3 in section 8 of the dieback
record, which says the factor "also multiplies fire mortality" without
qualifying which pools.

**There is a second AD regime boundary at model year 40.**
`FireMod.F90:586-594` switches the CWD contribution to `fuelc`:

```fortran
if (spinup_state == 1 .and. kyr < 40) then
   fuelc(c) = fuelc(c) + decomp_cpools_vr(c,j,i_cwd)*dzsoi_decomp(j)*spinup_factor(i_cwd)
else if (spinup_state == 1 .and. kyr >= 40) then
   fuelc(c) = fuelc(c) + decomp_cpools_vr(c,j,i_cwd)*dzsoi_decomp(j)*spinup_factor(i_cwd)/scalaravg_col(c,j)
```

Together with **nitrogen** limitation resuming at year 26, that puts **two**
configuration-driven regime changes inside the first 80 years. Only nitrogen
resumes: `lnd_in` in this case lineage has `suplnitro = 'NONE'` and
`suplphos = 'ALL'`, so phosphorus stays supplemented throughout AD and
`FPG_P` is 1.000 in every window of the 522677 analysis. Confirm both settings
against the rerun case's own `lnd_in` rather than inheriting them from here.

Annual output has to span both boundaries, which independently justifies a
diagnostic window of at least 60 years and comfortably supports 80.

**`use_nofire` is a clean global switch.** `FireMod.F90:652` zeroes
`farea_burned`, `baf_crop`, `baf_peatf`, `fbac` and `fbac1` together. It is a
domain-wide perturbation, not a targeted one.

### 1.4 The 0.5 degree rerun is already correctly configured (**measured**)

Job 522678, `20260910_seus_halfdeg_ad_spinup`, running at the time of writing:
`ELM_BLDNML_OPTS` ends in `-bgc_spinup on`, `lnd_in` has `spinup_state = 1`,
`nyears_ad_carbon_only = 25`, `spinup_mortality_factor = 10`, and annual output
on both tapes (`hist_nhtfrq = -8760,-8760`, `hist_mfilt = 20,20`) with
`STOP_N = 20`, `RESUBMIT = 0`. The failure mode that produced the
never-was-AD 0.5 degree chain is not present in this case.

---

## 2. Measured cost and storage basis

All from job 522626, which is a 4 km AD spin-up with annual dual-tape output —
the same shape as the proposed diagnostic.

| quantity | value |
|---|---|
| throughput, 20 nodes | 30 model years in 02:17:54, i.e. **13.0 model-yr/h** |
| `h1` patch-vector tape, 62 fields | 21.96 GB / 30 yr = **732 MB per model year** |
| `h0` gridded tape, 62 fields | 2.446 GB / 30 yr = **81.5 MB per model year** |
| per field, per year, on `h1` | **11.8 MB** |
| per field, per year, on `h0` | **1.3 MB** |

Extrapolations from those rates (**inference**, linear in years; I/O is a small
fraction of wall time, so the scaling should hold):

| run | years | wall time, 20 nodes | `h1` at 62 fields | `h1` at 34 fields |
|---|---|---|---|---|
| full AD | 200 | ~15.4 h | ~146 GB | ~80 GB |
| annual first 80 yr only | 80 | ~6.2 h | ~59 GB | ~32 GB |
| no-fire counterfactual | 40 | ~3.1 h | ~29 GB | ~16 GB |

**Those columns are the `h1` tape only and are not a resource request.** A
formal estimate has to add, at minimum:

| item | measured or derived | 200-year AD |
|---|---|---|
| `h0` gridded annual, 34 fields | 1.3 MB per field-year, measured | ~9 GB |
| `h3` instantaneous state, 7 fields | 11.8 MB per field-year, derived | ~17 GB |
| `elm.r` restart, 4 km | **14.85 GB each**, measured from job 522626 | depends on `REST_N` |
| `cpl.r` and `rpointer` | 4.0 MB each, measured | negligible |
| build directory | not measured | to be added |

The restart term dominates any estimate and is controlled entirely by `REST_N`.
At `REST_N = 20` a 200-year AD keeps 10 restarts, about 149 GB, more than the
entire history output. Decide `REST_N` and whether old restarts are pruned
before quoting a total.

Storage context: `/scratch` currently holds 16.79 T for this user with no block
quota set (**measured**, `lfs quota -u zw5 /scratch`). An 80-90 GB diagnostic
tape is about half a percent of that. The binding constraint on scratch is the
90-day atime purge, not capacity.

**Recommendation.** Write annual output for the entire 200-year AD rather than
switching frequency at year 80. The extra cost is roughly 48 GB against a
trimmed-field 80-year tape, and it removes a mid-chain `user_nl_elm` edit — the
kind of step that has already cost this project a silent `case.setup --reset`
namelist wipe. Post-process the annual records into 20-year means offline so
they line up exactly with the historical windows.

---

## 3. Experiment set

### 3.1 Experiment A — the production 4 km AD rerun, instrumented (required)

This is the user's proposal 1 and it is the right call: the AD stage has to be
rerun regardless, and the instrumentation is nearly free. One configuration
principle: change nothing except the two fixes and the output specification, so
that the comparison against the 2026-05-19 reference and against job 522373
stays interpretable.

Required settings, each with a reason:

| setting | value | why |
|---|---|---|
| source | current `SRCROOT`, rebuilt | must carry the 2026-07-17 HDM patch; a `--keepexe` clone would silently reuse the broken reader |
| `ELM_BLDNML_OPTS` | append `-bgc_spinup on` | the 0.5 degree chain's exact failure |
| `spinup_state` | 1, verified in `CaseDocs/lnd_in` before submit | as above |
| fire | on, `use_nofire` absent | reference configuration; this run must be usable as the production AD |
| `spinup_mortality_factor` | 10 | reference configuration |
| `nyears_ad_carbon_only` | 25 | reference configuration |
| `metdata_bypass` | `cpl_bypass_full`, checksum recorded at submit | proves which mapping table the run actually read |
| start | cold, `RUN_STARTDATE = 1-01-01` | no existing 4 km restart is usable; they all carry stranded evergreens |
| `hist_dov2xy` | `.true.,.false.` | `h0` gridded for input checks, `h1` patch vector for per-PFT work |
| `hist_nhtfrq` | `-8760,-8760,-8760` | annual; 20-year means are reconstructed offline |
| third tape | `hist_fincl3` with `:I` fields, `hist_dov2xy(3) = .false.` | year-end state, without which the leaf budget cannot be closed strictly |

Open for the user to set, deliberately not chosen here: `STOP_N`, `REST_N`,
`RESUBMIT`, node count, and `-p`/`-q` pairing.

### 3.2 Experiment B — no-fire counterfactual (conditional, and shorter)

**Decided: not now.** No no-fire run is scheduled at this stage merely to split
fire from the other loss terms. Experiment A's per-PFT fire fluxes do that
directly. The counterfactual is held in reserve for a different question, which
is whether removing fire would have prevented the stranding, and that question
only becomes worth paying for under the conditions below.

**Trigger conditions.** Experiment A's per-PFT fire fluxes give the proximate
loss term directly, per patch, per year. If the fire share of `LEAFC_LOSS`
dominates in the decline years and the fire year precedes or coincides with the
leaf carbon drop patch by patch, fire is established as the proximate cause of
leaf loss without any counterfactual. Run B only if that test comes out
ambiguous, or if the 405 are still stranded after the combined fix.

**Start it at 40 years, with an explicit extension condition.** Forty years is a
first block, not a claim of coverage. Two reasons it may not be enough. The
522373 trajectory still moves after year 40: 382 of 405 patches are below
threshold in the 21-40 window and 395 by 41-60, so the transition is not
complete at year 40. And the AD fuel formula switches at `kyr = 40`, so a run
that stops there observes essentially none of the post-switch response, which
is the part of the fire regime the second half of AD actually runs under.

Plan it as 40 years with a decision point, extending to 60 or 80 if the
stranded fraction is still changing at year 40 or if the post-switch fire
response matters to the conclusion. Costs scale linearly from section 2.

Keep the pairing strict: clone Experiment A, `--keepexe`, change only
`use_nofire = .true.`, same cold start, same forcing, same field list.

Two limits to state whenever its result is used. `use_nofire` zeroes burned
area across the whole domain, so it is not a targeted perturbation of the 405.
And it also removes the AD fuel-amplification pathway, so the contrast is
"reference AD" against "reference AD with no fire at all", not "fire" against
"no fire" holding everything else fixed.

### 3.3 Experiment C — read job 522626 (required, no new model run)

Analysis only, on output that already exists. It carries the coastal check and
the annual collapse timeline. Details in section 6.

---

## 4. Output fields

All names below were read out of `data_types/VegetationDataType.F90` in the
current `SRCROOT`. Every one is `hist_addfld1d` with `ptr_patch`, so they land
on the `h1` patch vector when `hist_dov2xy(2) = .false.`. Fluxes are
**gC/m^2/s**, states **gC/m^2**, both per unit patch area. Annual means convert
with x 86400 x 365 for a no-leap calendar — confirm the calendar from the run's
own time attributes rather than assuming it.

Marked **[i]** = registered `default='inactive'`, so it is absent unless named
in `hist_fincl`. That is the entire reason job 522626 cannot close the fire
question.

**Year-end state, required for a strict budget.** Verified in
`main/histFileMod.F90`: a per-field averaging flag is parsed from a `:` suffix
in `hist_fincl` (`getname`/`getflag`, lines 4335 to 4380), `'I'` is an accepted
flag (line 540), and `hist_avgflag_pertape` sets a whole-tape default (line
81). So the state snapshots come from a third tape, written annually with
instantaneous sampling:

```
hist_fincl3 = 'LEAFC:I', 'LEAFC_STORAGE:I', 'LEAFC_XFER:I', 'CPOOL:I',
              'XSMRPOOL:I', 'TLAI:I', 'TOTVEGC:I'
hist_nhtfrq(3) = -8760 ;  hist_mfilt(3) = 200 ;  hist_dov2xy(3) = .false.
```

Seven patch-vector fields is about 83 MB per model year, roughly 17 GB over 200
years. A snapshot at the annual boundary pairs with the averaged fluxes of the
year that just ended, and that is what turns the flux identity into a checkable
state budget. Confirm the snapshot's timestamp convention against the first
written record instead of assuming which side of the boundary it lands on.

**Leaf carbon budget, the flux set.** With the snapshots above, these close
the budget. The identity they satisfy at each time step is
`d(LEAFC)/dt = LEAFC_ALLOC - LEAFC_LOSS` exactly.

```
LEAFC  LEAFC_STORAGE  LEAFC_XFER  TLAI
LEAFC_ALLOC  LEAFC_LOSS
LEAFC_XFER_TO_LEAFC [i]   CPOOL_TO_LEAFC   LEAFC_TO_LITTER
M_LEAFC_TO_LITTER [i]     M_LEAFC_TO_FIRE [i]   M_LEAFC_TO_LITTER_FIRE [i]
M_LEAFC_STORAGE_TO_FIRE [i]   M_LEAFC_XFER_TO_FIRE [i]
```

**Supply side, to separate "burned off" from "never grew".**

```
GPP  NPP  AR  MR  GR  XR  CPOOL  XSMRPOOL
AVAILC  PLANT_CALLOC  EXCESS_CFLUX [i]
```

`XR` has its own field and is also recoverable as `AR - MR - GR`; carrying both
gives a free consistency check on the tape itself.

**Limitation and stress.**

```
BTRAN  FPG  FPI  FPG_P  FPI_P  SMINN  LEAFN  RETRANSN
```

`FPG`, `FPI` and `SMINN` are column-level, so on the `h1` vector they are
written on the column axis, not the patch axis, and have to be joined by column
index. The 522677 analysis already does this join; reuse that code rather than
re-deriving it.

**Fire and input verification.**

```
COL_FIRE_CLOSS  HDM  LNFM  FAREA_BURNED
TBOT  FSDS  TOTVEGC  TOTSOMC  DEADSTEMC
```

`HDM`, `TBOT` and `FSDS` must be on the **`h0`** gridded tape as well, since the
G1 checks are per land cell, not per patch.

That is 34 distinct `h1` fields, which is where the 34-field storage column in
section 2 comes from.

---

## 5. Acceptance criteria

Deliberately none of these is a domain mean, and none rests on a single early
window. Every criterion names its population and its window.

### C1 — coastal forcing (G1, blocking)

1. On every complete annual `h0` record, **excluding year 0001**: the count of
   land cells with annual-mean `FSDS < 1 W/m2`, or annual-mean `TBOT` outside
   -30 to +45 C, must be **exactly 0**. The current count is 194.
2. At the 194 historically affected cells specifically: `GPP > 0` in every year
   after year 1, and `TBOT`/`FSDS` inside the range spanned by their valid
   neighbours. Per cell, not averaged.
3. The `zone_mappings.txt` actually read by the run must match the repaired
   table by checksum. Record the checksum in the case log at submit time.
4. Reconcile the 194 / 193 / 193 count discrepancy flagged as pending in the
   dieback record before declaring full coverage: 194 zero-GPP land cells, 193
   sentinel-associated pine patches, 193 changed mappings. Patch and gridcell
   counts legitimately differ, but that does not explain 194 against 193.

Any cell failing 1 or 3 stops the chain. No vegetation conclusion from a run
with sentinel forcing is worth drawing.

### C2 — HDM (G1, blocking)

1. `HDM` on `h0` has a spatial mean near 5.1 (the 522373 reference value), a
   minimum of at least 0, and a spatial pattern matching the input file. Zero
   everywhere means the wrong executable.
2. The case `EXEROOT` build post-dates 2026-07-17, and the `SRCROOT` git commit
   hash is recorded in the case record.

### C3 — per-PFT vegetation state (G2)

Report on 20-year means reconstructed offline from the annual records, so the
windows line up with 1-20, 21-40, ..., 181-200 and are directly comparable with
the control and with job 522373.

For each PFT, and separately for three populations — whole domain, the Florida
box, and everything south of 26 N where 42.4% of pine was stranded — report
**three classes, never one**:

- fraction with `LEAFC` exactly 0,
- fraction with `LEAFC > 0` but `TLAI < 0.5` (surviving low-LAI),
- fraction healthy, plus the median LAI.

That three-way split is the dieback record's own open item; cohort means over a
bimodal population are the specific error that produced two retracted
conclusions.

Screening expectations, stated as thresholds for a conversation, not as pass
marks:

| population | expectation in the 61-80 window | pause if |
|---|---|---|
| pine, whole domain | at or below ~1%; HDM-only measured 0.9%, non-sentinel arithmetic 0.589% | above ~2% |
| pine, south of 26 N | must be reported explicitly; no prior combined-fix value exists | comparable to the 42.4% seen before |
| the 405 tracked patches | reported explicitly by `(lat, lon, PFT)` from `residual_trajectory.csv` | still stranded at a similar rate |
| the 193 sentinel patches | at least 90% above `TLAI` 1.0, mirroring the 90.4% recovery job 522373 showed for the control's stranded set | below that |
| broadleaf evergreen shrub | assessed on its own; 22.6% under HDM-only is not a target | no separate assessment made |

Track patches by `(lat, lon, PFT type)`, not by raw `pft_index`. The index is
only stable while the surface dataset and patch ordering are identical, and
that is an assumption the rerun should not silently inherit.

### C4 — leaf carbon budget closure and attribution (G3)

1. **Closure, from year-end state, not from annual means.** For every tracked
   patch and year, compare `LEAFC(end of year) - LEAFC(end of previous year)`
   taken from the instantaneous `h3` tape against
   `(LEAFC_ALLOC - LEAFC_LOSS) * seconds_in_year` taken from the averaged `h1`
   tape. Report the residual distribution, not a mean, and report it separately
   for collapsing and healthy patches.

   A difference of two annual **means** is not the year's change in state and
   must not be substituted for this. Where only averaged output exists, say so
   and label the result an approximate consistency check.

   Known legitimate residual sources, to be quantified rather than assumed
   away: `PrecisionControlMod` truncation of very small leaf carbon, which is
   most active in exactly the collapsing patches; any patch-weight transfer; and
   `hrv_leafc_to_litter`, which has no history field. Do not attribute the
   residual to any one of them without a separate test. A systematically large
   residual means a missing term and invalidates the attribution built on it.
2. **Attribution.** In the years where `LEAFC` falls fastest, per patch,
   compute the share of `LEAFC_LOSS` carried by
   `M_LEAFC_TO_FIRE + M_LEAFC_TO_LITTER_FIRE`, by `LEAFC_TO_LITTER`, and by
   `M_LEAFC_TO_LITTER`. Fire is established as the proximate cause when the
   fire share dominates in the decline years and the fire year precedes or
   coincides with the drop, patch by patch. Cohort ratios do not settle this.
3. **Supply-side alternative.** On the same annual axis, check whether
   `LEAFC_ALLOC`, `AVAILC` and `CPOOL` collapse *before* fire rises. If they do,
   the cause sits on the supply side and the fire signal is a consequence.
4. **Confounders on the same axis.** Plot `FPG` (changes at year 26), `BTRAN`,
   and mark year 40 where the AD fuel formula switches. Any timing claim that
   ignores those two boundaries is not safe.

### C5 — stability (G2, gate to the next stage)

1. Across the last three AD windows (141-160, 161-180, 181-200) the per-PFT
   stranded fraction must not increase, for each of the three populations in
   C3. A flat low number over three windows is the direct analogue of the
   evidence that the old chain locked at 9.0-9.1% and never moved.
2. At the end of final spin-up: verify restart `spinup_state` metadata and the
   per-pool AD-exit transformation, then end drift below about 1% per century,
   **and re-run C3**. A converged soil under a re-stranded canopy is still a
   failed stage.

---

## 6. Analysis to run on job 522626 (no new model run)

One batch job, reading output that already exists.

1. **Coastal, on `h0`:** for every annual record from year 2 on, count land
   cells with `FSDS < 1` or `TBOT` outside the physical range; expect 0. At the
   194 historically affected cells report per-cell `GPP`, `TBOT`, `FSDS`.
   This is C1 applied to a run that is not the production one, which is exactly
   why it is useful: it isolates the mapping fix from the HDM fix.
2. **Annual collapse timeline, on `h1`:** for the 405 and the 193, per year,
   `TLAI`, `LEAFC`, `GPP`, `NPP`. Produces the first-year-below-threshold
   distribution that 20-year means cannot give, and tests the
   "establish first, then fail" statement the dieback record downgraded.
3. **Budget, plus an explicit inventory of what this output cannot close.**
   Every field on both tapes is `avgflag='A'`, so no year-end state exists
   except in one place: the single restart `elm.r.0031-01-01`, **measured** at
   14.85 GB, written because `REST_N = 30`. That is one exact anchor, at the
   end of the run.

   Report three categories separately. Checkable now, and labelled approximate:
   `LEAFC_ALLOC - LEAFC_LOSS` against the year-to-year change in annual-mean
   `LEAFC`, plus `LEAFC_LOSS - LEAFC_TO_LITTER` as one lumped non-litterfall
   loss term. Checkable once, at year 31, against the restart state. Not
   answerable from this run at all, and needing the `h3` instantaneous tape from
   Experiment A: strict per-year closure, and the size of the
   `PrecisionControl` truncation term. That inventory is a deliverable of this
   job, not a footnote.
4. **XR read, not merely recovered.** Compute `AR - MR - GR` per patch per year,
   then report its magnitude before, during and after the decline, alongside
   `CPOOL`, `XSMRPOOL` and `TBOT`. Recovering the flux closes the missing-field
   problem only. Whether excess respiration contributes to the decline needs
   these comparisons, and they are what this job should deliver.

Its stranded fractions are control values under the unfixed HDM. They must
never be quoted as a repaired outcome.

---

## 7. Gates

**Proceed from AD to final spin-up when** C1 reports zero affected cells, C2
passes, C4 closes, C3's pine fraction is at or below roughly 1-2% domain-wide
with the south-of-26 N and Florida numbers not an order of magnitude worse, and
C5.1 shows no increase across the last three windows.

**Proceed to transient** only after the final spin-up passes C5.2, which
includes re-running C3 at that stage.

**Proceed to the future scenarios** only after the transient passes C3 at 2023
and the four `future_clim/ssp*` mapping tables are checksum-matched to the
repaired versions.

**Pause and investigate when** any of these appear:

- a land cell still reads a sentinel, or the mapping checksum does not match;
- `HDM` is zero or the wrong magnitude, meaning the wrong executable;
- the pine stranded fraction rises across the last three AD windows;
- the 405 remain stranded at a comparable rate after the combined fix — this is
  the specific trigger for Experiment B;
- the leaf budget does not close, since every attribution statement rests on it;
- broadleaf evergreen shrub stays near its 22.6% HDM-only value, which is a
  separate problem from pine and must not be waved through on pine's number.

---

## 8. What this plan does not establish

- No combined-fix vegetation result exists yet. The 0.589% figure is the
  non-sentinel subset of an HDM-only experiment, arithmetic rather than
  measurement.
- Nothing here changes evergreen phenology. The fixes remove triggers; the
  absorbing state in `CNEvergreenPhenology` remains, and any future cold start
  with a different disturbance regime can strand evergreens again.
- Job 522626's output has **not** been read. Its coastal result is an
  expectation from the static replay, not a measurement, until section 6 runs.
- Removing configuration errors does not demonstrate agreement with observed
  GPP or biomass. That is a separate evaluation against data.
