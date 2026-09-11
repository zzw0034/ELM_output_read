# 4 km AD rerun: verified configuration, ready to execute

Read-only preparation completed 2026-09-10. Nothing was created, modified or
submitted. Companion to [RERUN_VERIFICATION_PLAN.md](RERUN_VERIFICATION_PLAN.md),
which says what to measure; this file says what to build.

The authoritative build checklist is `elm_setup_and_run_guide.md` at the
workspace root. Where this file and that one differ, that one wins.

## 1. Source and executable

| item | verified value |
|---|---|
| `SRCROOT` | `/projects/hpcl-cli185/proj-shared/zw5/E3SM` |
| branch / HEAD | `master` at `17efedae5f057782397e1a026cee40ff776f90ab` |
| HDM reader fix | present: the hardcoded `hdm1(720,360,1)` declaration is commented out at `lnd_import_export.F90:105`, and a `check_netcdf_status` helper at line 1831 is called after every HDM netCDF operation |
| cpl_bypass index fixes | present: the two most recent commits touching that file are `3cf28db19f` clamping the restart forcing index and `fc2a4f2be1` guarding the transient-window overrun |

**The build must be fresh.** A `--keepexe` clone would reuse an executable built
before 2026-07-17 and silently reinstate the zero-HDM bug. Record the `SRCROOT`
commit hash in the case directory at build time.

## 2. Reference configuration, all paths verified to exist

Taken from `20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup`,
which is the closest thing to a clean reference.

| namelist item | path | size |
|---|---|---|
| `fsurdat` | `.../e3sm_run/20260712_Southeast_hires_s7P_s8hdm_ICB1850CNRDCTCBC_ad_spinup/run/surfdata.nc` | 1.4 G |
| `paramfile` | same directory, `clm_params.nc` | 88 K |
| `fsoilordercon` | same directory, `CNP_parameters.nc` | 4.5 K |
| `stream_fldfilename_popdens` | `.../ELM_makeSurfdata/Make_surface_data/s8_update_hdm/elmforc.Li_hdm_1_24x1_24_bilinear_SEUS_simyr1850-2100.nc` | 68 M |
| `metdata_bypass` | `.../Daymet_ERA5_TESSFA2/cpl_bypass_full` | repaired mapping, 117,964 rows |
| domain | `.../e3sm_run/20260712_.../run/domain.nc`, reached through a **symlink in RUNDIR** | |

Nitrogen deposition is `stream_year_first_ndep = stream_year_last_ndep = 1850`
in this lineage, so the stale-2005 problem recorded for the transient case does
not apply to the AD stage. Population density is likewise 1850/1850.

**The domain trap.** `LND_DOMAIN_PATH` is empty and `ATM_DOMAIN_FILE` is the
bare name `domain.nc`, which GETFIL resolves against RUNDIR. A fresh RUNDIR dies
in about 22 seconds on `GETFIL: FAILED to get /domain.nc` until the file is
symlinked in. Stage it before the first submit.

## 3. Recommended run parameters

All five, with the evidence behind each. Throughput is measured, not assumed.

| measurement | value | source |
|---|---|---|
| 20 nodes, `parallel` + `BL`, annual dual-tape output | **13.05 model-yr/h** | job 522626, 30 yr in 02:17:54 |
| 12 nodes, dedicated partition, 20-year-mean output | 6.24 model-yr/h | job 522373, 80 yr in 12:49:30 |
| per node | 0.652 against 0.520 model-yr/h | the same two jobs |
| memory actually needed | about 75 g per node | `elm_setup_and_run_guide.md` §16.0 |
| one `elm.r` restart, 4 km | **13.83 GiB**, 14.85 GB | job 522626 |
| `elm.rh0` / `elm.rh1` | effectively zero | job 522626 |
| one `h1` field, one model year | 11.8 MB | job 522626 |
| one `h0` field, one model year | 1.3 MB | job 522626 |

### The recommendation

| parameter | value | unit |
|---|---|---|
| nodes | **20** | `NTASKS = 2560` for every component, `MAX_TASKS_PER_NODE = 128` |
| partition / QoS | **`-p parallel -q hpcl-cli185`** | with `--mem=200g --constraint=BL`, no `--exclude` |
| `STOP_OPTION` / `STOP_N` | **`nyears` / 50** | 4 segments of 50 model years |
| `RESUBMIT` | **3** | segments minus one |
| `REST_OPTION` / `REST_N` | **`nyears` / 25** | 8 restarts, at model years 25 through 200 |
| `JOB_WALLCLOCK_TIME` | **08:00:00** | about 2.1 times the estimated 3.83 h per segment |

Total: 200 model years, about **15.3 h** of compute across 4 segments.

### Why each value

**20 nodes on `parallel`, not the dedicated partition.** The parallel pool under
the `BL` constraint measured faster per node than the dedicated partition did,
0.652 against 0.520 model-yr/h. It also leaves the 20-node dedicated partition
free rather than occupying all of it for 16 hours. `-q hpcl-cli185` is required
because `normal` caps a user at 2000 CPUs and 2560 would pend forever.
`--constraint=BL` avoids the 84-core `pfc` nodes and their mixed-generation
InfiniBand, which hangs E3SM. `--mem=200g` filters unusable node specs while
keeping 138 nodes eligible; 400 g would cut that to 70 and buy nothing, since
the real need is about 75 g. Validated with `sbatch --test-only`, which
allocated 2560 processors on `blc[081-093,095-101]`.

**Segment length 50 years.** This trades queue waits against failure loss. Four
segments of 3.83 h lose at most 3.83 h of compute to a crash and take four
queue waits. Eight segments of 25 years would halve the loss and double the
waits. Fifty years is the middle, and it keeps the whole run inside one working
day if the queue cooperates.

**Restart every 25 years, not every segment and not every year.** History
frequency and restart frequency are deliberately decoupled. Annual diagnostics
need no annual restart; the leaf budget is closed by the instantaneous history
tape in section 4, not by restart files. `REST_N = 25` gives one restart at each
segment boundary, which resubmission requires, plus one mid-segment, which caps
a crash at about 1.9 h of lost compute. `STOP_N` must stay an integer multiple
of `REST_N`, and 50 is 2 times 25. Year 25 also happens to be the end of the
carbon-only phase, so one exact state lands on that boundary for free.

Restart storage is the price: 8 sets at 14.85 GB is **119 GB**. Choosing
`REST_N = 50` would cut that to 59 GB and raise the worst-case loss to 3.83 h.
Do not assume the full set survives: `elm_setup_and_run_guide.md` §15.9 records
a case that kept 7 restarts at roughly 29-year spacing against a documented
`REST_N = 20`. Check with `ls $RUNDIR/*.elm.r.*.nc` before relying on any of
them.

### Total storage

| item | fields | per model year | 200 years |
|---|---|---|---|
| `h1` patch vector, annual mean | 34 | 401 MB | 80 GB |
| `h0` gridded, annual mean | 34 | 44 MB | 9 GB |
| `h2` patch vector, annual instantaneous | 7 | 83 MB | 17 GB |
| `elm.r` restarts | | | 119 GB |
| **total** | | | **about 225 GB** |

Against 16.79 T already on `/scratch` with no block quota, this is about 1.3%.
The build directory is not included and was not measured.

## 4. The three history tapes

Tape numbering is offset by one: `hist_fincl1` writes `.h0.`, `hist_fincl2`
writes `.h1.`, and `hist_fincl3` writes `.h2.`. The instantaneous tape is
therefore **h2**, not h3.

```
 hist_empty_htapes = .true.
 hist_dov2xy   = .true., .false., .false.
 hist_nhtfrq   = -8760, -8760, -8760
 hist_mfilt    = 50, 50, 50
```

`hist_mfilt = 50` matches `STOP_N`, so each segment writes one file per tape.

**Tape 1, `hist_fincl1`, gridded**: keep the reference 57-field list unchanged
and add `FAREA_BURNED`. `HDM`, `TBOT` and `FSDS` are already in it, which is what
the coastal and HDM checks read.

**Tape 2, `hist_fincl2`, patch and column vectors**: the reference list plus the
fields below. Marked `[i]` means registered `default='inactive'`, so it is absent
unless named. That is exactly why job 522626 could not split fire from
background mortality.

```
'XR', 'XSMRPOOL', 'AVAILC', 'PLANT_CALLOC', 'EXCESS_CFLUX',
'LEAFC_STORAGE', 'LEAFC_XFER', 'LEAFC_ALLOC', 'LEAFC_LOSS',
'LEAFC_TO_LITTER', 'LEAFC_XFER_TO_LEAFC', 'CPOOL_TO_LEAFC',
'M_LEAFC_TO_LITTER', 'M_LEAFC_TO_FIRE', 'M_LEAFC_TO_LITTER_FIRE',
'M_LEAFC_STORAGE_TO_FIRE', 'M_LEAFC_XFER_TO_FIRE',
'FAREA_BURNED', 'LEAFN', 'FROOTN'
```

**Tape 3, `hist_fincl3`, patch vector, instantaneous**:

```
'LEAFC:I', 'LEAFC_STORAGE:I', 'LEAFC_XFER:I', 'CPOOL:I',
'XSMRPOOL:I', 'TLAI:I', 'TOTVEGC:I'
```

The `:` suffix syntax is verified in `main/histFileMod.F90`: `getname` and
`getflag` at lines 4335 to 4380 parse it, and `'I'` is accepted at line 540.

## 5. Annual mean fluxes against year-end state

The distinction that makes the leaf budget checkable.

| quantity | tape | `avgflag` | units | meaning |
|---|---|---|---|---|
| `LEAFC_ALLOC`, `LEAFC_LOSS`, every `M_LEAFC_*` | h1 | `A` | gC/m^2/s | mean over the year |
| `LEAFC`, `CPOOL`, `TLAI` on h2 | h2 | `I` | gC/m^2 | state at the writing instant |
| `LEAFC` on h1 | h1 | `A` | gC/m^2 | mean over the year, **not** a state |

The closure to evaluate, per patch, per year:

```
LEAFC_h2[y] - LEAFC_h2[y-1]  ==  (LEAFC_ALLOC - LEAFC_LOSS)_h1[y] * 31,536,000
```

31,536,000 seconds is a 365-day no-leap year. Confirm the calendar from the
run's own `time:calendar` attribute rather than assuming it.

Verified in `data_types/VegetationDataType.F90:8410-8428`:

```
LEAFC_ALLOC = LEAFC_XFER_TO_LEAFC + CPOOL_TO_LEAFC
LEAFC_LOSS  = M_LEAFC_TO_LITTER + M_LEAFC_TO_FIRE + M_LEAFC_TO_LITTER_FIRE
            + LEAFC_TO_LITTER + HRV_LEAFC_TO_LITTER
```

Three residual sources to quantify rather than assume away. `hrv_leafc_to_litter`
has **no history field registered**; it should be zero here because the AD case
has no `flanduse_timeseries` and no `do_harvest`, and the residual will show if
it is not. `PrecisionControlMod` truncates very small leaf carbon to zero, which
removes carbon with no flux recording it, and is most active in exactly the
collapsing patches. Any patch-weight transfer also lands in the residual.

A difference of two annual **means** is not a state change. Job 522812 measured
what that substitution costs: at year 30 the annual mean exceeded the restart
state by 3.44 gC/m^2 on average for the 405, and in a fast-changing year the
apparent imbalance reached 72 gC/m^2.

## 6. Per-PFT fire and mortality fields, as defined in the source

All are `hist_addfld1d` with `ptr_patch`, units gC/m^2/s, and all are
`default='inactive'`.

| field | definition | source |
|---|---|---|
| `M_LEAFC_TO_FIRE` | `leafc * f * cc_leaf(itype)` | `FireMod.F90:1012` |
| `M_LEAFC_TO_LITTER_FIRE` | `leafc * f * (1 - cc_leaf(itype)) * fm_leaf(itype)` | `FireMod.F90:1083` |
| `M_LEAFC_STORAGE_TO_FIRE` | `leafc_storage * f * cc_other(itype)` | `FireMod.F90:1013` |
| `M_LEAFC_XFER_TO_FIRE` | `leafc_xfer * f * cc_other(itype)` | `FireMod.F90:1014` |
| `M_LEAFC_TO_LITTER` | background mortality | `VegetationDataType.F90:5963` |

`f` is the burned area fraction for the patch's column, so `FAREA_BURNED` on the
same tapes lets the flux be separated from the area driving it.

**Neither leaf fire term is multiplied by `spinup_mortality_factor`.** In
`FireMod.F90` the `m_veg` factor multiplies only dead stem and dead coarse root
combustion. The AD amplification reaches leaves indirectly, through `fuelc` and
therefore through `f`. The fuel formula itself switches at `kyr = 40`
(`FireMod.F90:586-594`), which is the second regime boundary inside the
diagnostic window, alongside nitrogen limitation resuming at year 26.

## 7. Operations, for approval

Nothing below has been run. Ordering matters; three of these steps exist only
because they have already failed once in this project.

1. **`create_newcase`** from `SRCROOT`, compset `ICB1850CNRDCTCBC`, custom SEUS
   grid, following `elm_setup_and_run_guide.md` §3.
2. **All `xmlchange` that can trigger `case.setup --reset`**: PE layout to
   `NTASKS = 2560`, domain settings, `ELM_BLDNML_OPTS` append `-bgc_spinup on`,
   `DOUT_S = FALSE`, `STOP_OPTION`/`STOP_N`/`REST_OPTION`/`REST_N`/`RESUBMIT`,
   `JOB_WALLCLOCK_TIME`.
3. **`BATCH_COMMAND_FLAGS` in `env_workflow.xml`**, all three subgroups, to
   `--time $JOB_WALLCLOCK_TIME -p parallel -A hpcl-cli185 -q hpcl-cli185 --mem=200g --constraint=BL`.
   Editing `env_batch.xml` looks like it works and changes nothing.
4. **`user_nl_elm`**: the reference settings of section 2 plus the three tapes of
   section 4.
5. **`case.setup`**, then confirm no further `case.setup --reset` will run.
6. **Append the CPL_BYPASS macro** to `cmake_macros/universal.cmake`, only now.
   A `case.setup --reset` after this point regenerates the directory and drops
   the macro with no error, and the case then builds fine and dies at coupler
   initialisation.
7. **`case.build`**, then verify the macro really compiled in with
   `zgrep -l 'CPL_BYPASS' $EXEROOT/e3sm.bldlog.*`. A successful build does not
   prove it.
8. **Symlink `domain.nc` into the new RUNDIR**, or the run dies in 22 seconds.
9. **Pre-submit verification**, read-only: `CaseDocs/lnd_in` shows
   `spinup_state = 1`, `nyears_ad_carbon_only = 25`,
   `spinup_mortality_factor = 10`, the three `hist_fincl` lists and the repaired
   `metdata_bypass`; `./preview_run` shows the intended `SUBMIT CMD`, since
   `case.setup --reset` silently resets `JOB_WALLCLOCK_TIME` to 24 h and the XML
   string will not reveal it; `CONTINUE_RUN = FALSE` and `RESUBMIT = 3`.
10. **`case.submit`**, recording the job ID and the `SRCROOT` commit hash.
11. **Five minutes after it starts, run `check_node_freq.sh`.** A node stuck at
    399 MHz reads as healthy to Slurm and cost this project 15 hours once.

Steps 1 through 8 create and modify files and compile. Step 10 submits. I will
run none of them until you confirm.
