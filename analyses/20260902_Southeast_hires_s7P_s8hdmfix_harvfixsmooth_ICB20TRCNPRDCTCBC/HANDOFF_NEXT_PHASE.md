# Handoff: SEUS 4 km rerun, next phase

Cold-start briefing, last updated 2026-09-11 14:40. Read this, then
[EVERGREEN_DIEBACK.md](EVERGREEN_DIEBACK.md) sections 5 and 7 for the evidence
and [RERUN_VERIFICATION_PLAN.md](RERUN_VERIFICATION_PLAN.md) for the gates.
Read the workspace `AGENTS.md` before any SSH, Slurm or sync action.

## 1. Where things stand

**The 4 km AD rerun is running and on track.** Case
`20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup`, the
first run with the corrected HDM reader **and** the repaired `zone_mappings.txt`
together. Cold start, 200 model years, 4 segments of 50, 30 nodes, 3840 ranks.

| job | segment | model years | state |
|---|---|---|---|
| 522838 | two-year smoke test | 1-2 | COMPLETED 00:11:28, moved aside into `run/smoketest_522838/` |
| 522930 | 1 | 1-50 | COMPLETED 03:07:20 |
| 523140 | 2 | 51-100 | COMPLETED 03:11:45 |
| 523228 | 3 | 101-150 | COMPLETED 03:20:46 |
| **523537** | **4** | **151-200** | **RUNNING**, at model year 159 as of 14:36 |

Roughly 15 to 16 model years per hour. Segment 4 should finish about 17:00 to
17:30 local. CIME resubmits on its own; `RESUBMIT` has been consumed down, so
after segment 4 the chain simply stops.

**First thing to do: check whether it finished.**

```bash
ssh pathfinder "sacct -j 523537 --format=JobID%8,State,Elapsed,End -X"
```

| item | path |
|---|---|
| CASEROOT | `/projects/hpcl-cli185/proj-shared/zw5/e3sm_cases/20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup` |
| RUNDIR and EXEROOT | `/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/<case>/{run,bld}` |
| durable inputs | `/projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/` |
| analysis code and docs | `ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/` |
| provenance | `PROVENANCE.txt` in CASEROOT: SRCROOT `17efedae5f`, clean tree, exe md5 `b882ff67cf805c0ab95495890ffea1ec` |

The 0.5 degree chain is running independently and is already in final spin-up.

## 2. What is settled, so it is not re-litigated

- **Both input fixes verified in one run.** `HDM` domain mean 5.128131 against
  the 5.128 of job 522373; zero of 75,920 land cells on sentinel forcing, against
  194 before.
- **The 193 coastal patches recovered fully**, TLAI 1.962 at year 49 against
  1.977 for healthy pine.
- **The 405 residual patches do not recover**, TLAI 0.032, and the reason is
  measured: their 1850 population density median is 0.048 against 4.162 for
  healthy pine, so HDM fire suppression cannot reach them.
- **The mechanism is measured, not inferred.** In the same gridcells and the same
  fires, pine's `LEAFC_STORAGE` and `LEAFC_XFER_TO_LEAFC` are exactly zero every
  year because `fcur = 1` sends all allocation to displayed leaf; deciduous has
  `fcur = 0` and rebuilds from storage independent of standing leaf area.
- **The leaf budget closes to 0.000 gC/m^2 per year** using the instantaneous
  `h2` tape, which is what licenses the fire split: fire is 31 to 37 percent of
  leaf loss in decline years against 1 to 4 percent in quiet ones.
- **Decision taken: the residual is accepted**, at 0.42 percent of domain pine
  carbon area-weighted. A mask file exists. The no-fire counterfactual is **not**
  scheduled. See section 5 of the dieback record for the usable and not-usable
  boundaries.

## 3. Immediate next actions

**A. Final acceptance of the AD stage, when it finishes.** This is the gate to
everything downstream. Both scripts live in this directory and are already
synced to the Pathfinder copy; submit them with their `run_*.slurm` wrappers,
which target `serial` and `normal` and take well under a minute each. Note that
`analyze_combined_fix.py` currently reads only the **first** closed segment file
so it never touches a file being written; with the run finished, drop that
restriction so it merges all four segment files per tape.

1. `verify_smoketest.py` on the final output, for HDM, sentinel forcing, field
   completeness, `h2` against the restart at a matching date, and volume.
2. `analyze_combined_fix.py` with no `--max-year`, for the per-PFT
   classification by window and region and the tracked-group trajectories.
3. **The gate**: per-PFT stranded fraction must **not increase** across the last
   three 20-year windows, 141-160, 161-180, 181-200, for the whole domain, the
   Florida box and south of 26 N separately. The old chain locked at 9.0 to 9.1
   percent and never moved; a flat low number over three windows is the
   equivalent evidence that this one is stable.
4. Also check the AD-exit prerequisites: `spinup_state` in the final restart, and
   that the restart set is actually complete (`ls $RUNDIR/*.elm.r.*.nc`; do not
   trust `REST_N` arithmetic, see the setup guide section 15.9).

**B. Final spin-up, only after A passes.** Two things make it different from AD
and both have bitten this project:

- It is the **first** stage with prognostic phosphorus. AD runs the CN compset
  with `suplphos = 'ALL'`; final spin-up is CNP with `suplphos = 'NONE'`. A clean
  evergreen result at the end of AD is **not** evidence it survives that switch.
  Report `FPI_P` and `FPG_P` alongside the per-PFT check there.
- Verify the per-pool AD-exit transformation actually fired. `exit_spinup` only
  triggers when a `spinup_state = 0` run reads a `spinup_state = 1` restart. The
  0.5 degree chain failed exactly here and nothing complained.

Acceptance for that stage: soil carbon end drift below about 1 percent per
century, **and** the per-PFT check re-run. A converged soil under a re-stranded
canopy is still a failed stage.

**C. Then transient 1850-2023, then the seven future scenarios.** The future
`ssp*` mapping tables were repaired at the same time as the historical one, so
they pick up the fix automatically; verify by checksum, do not assume.

## 4. Traps that have already cost time here

- `case.setup --reset` silently reverts `JOB_WALLCLOCK_TIME` to 24 h and
  regenerates `cmake_macros/`, dropping `-DCPL_BYPASS`. Always add the macro
  **after** the last `case.setup`, and verify with
  `zgrep -l 'CPL_BYPASS' $EXEROOT/e3sm.bldlog.*` against the log that actually
  produced the running executable. Check the real settings with `./preview_run`,
  not the XML string.
- `BATCH_COMMAND_FLAGS` lives in `env_workflow.xml`. Editing `env_batch.xml`
  looks like it works and does nothing.
- A fresh RUNDIR needs `domain.nc` symlinked in, or the job dies in 22 seconds on
  `GETFIL`.
- **History tape numbering is offset**: `hist_fincl1` writes `.h0.`, `fincl2`
  writes `.h1.`, `fincl3` writes `.h2.`.
- **`hist_mfilt` counts records, not years**, and the model writes a short
  initialisation record first. With `hist_mfilt = 50` and `STOP_N = 50` the first
  file holds 49 full years and year 50 spills into the next. Never read a record
  index as a model year: derive it from `mcdate` minus one, and reject any record
  whose `time_bounds` do not span a full calendar year. Merge all files of a tape.
- **Run OLMT as the reference for any ELM case setting.** It sets both
  `-bgc_spinup on` and `suplphos = 'ALL'` from the same substring test on the
  case name, so a case not named `*ad_spinup*` silently loses both.
- Five minutes after any production job starts, run `check_node_freq.sh` under
  load. A node stuck at 399 MHz reads as healthy to Slurm and cost 15 hours once.
- Per-PFT fire and mortality fields are `default='inactive'`. `FAREA_BURNED` is
  registered on the **column**, not the patch.

## 5. Standing constraints

Never quote a domain mean alone for anything evergreen. Report the whole domain,
the Florida box and south of 26 N separately, and split low-LAI three ways into
zero leaf carbon, surviving low-LAI and healthy. Two retracted conclusions in the
record came from means over a bimodal population.

Exclude or flag `stranded_pine_mask_SEUS_1_24deg.nc` in any regional pine
statistic, and be careful with management scenarios: those cells hold almost no
pine leaf carbon, so a treatment signal is absent rather than cancelling.

Storage for the AD stage is about 320 GB on scratch, which is subject to the
90-day purge. The 4 km transient and futures are the deliverable and must not end
up living only there.
