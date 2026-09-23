# Case matrix — manuscript cohort (20260910 rerun)

Built 2026-09-23 from read-only inspection of Pathfinder (`lnd_in`,
`env_*.xml`, history headers, file timestamps). Cohort decision: blueprint
"Decisions — 2026-09-23". This file is the only place case names should be
copied from; `common.py` must be switched to it.

Output root (scratch, purgeable):
`/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/<case>/run/`
CASEROOT: `/projects/hpcl-cli185/proj-shared/zw5/e3sm_cases/<case>/`

## 1. The matrix — 34 cases, all complete

Every future case has 77 monthly h0 files (2024–2100) and 77 h1 (PFT) files;
each transient has 174 (1850–2023). The last file of every case holds all 12
monthly records. History: `hist_nhtfrq=0,0`, `hist_mfilt=12,12` (h0 gridcell,
h1 PFT; monthly). No h2.

### 0.5° (`dt3600` family)

| | SSP1-1.9 | SSP2-4.5 | SSP3-7.0 | SSP5-8.5 |
|---|---|---|---|---|
| Default | `20260911_seus_halfdeg_future_ssp119_dt3600` | `20260911_…_ssp245_dt3600` | `20260911_…_ssp370_dt3600` | `20260911_…_ssp585_dt3600` |
| RF | `20260915_seus_halfdeg_future_ssp119_RF_dt3600` | `20260915_…_ssp245_RF_dt3600` | `20260911_…_ssp370_RF_dt3600` | `20260915_…_ssp585_RF_dt3600` |
| RH | `20260915_…_ssp119_RH_dt3600` | `20260915_…_ssp245_RH_dt3600` | `20260911_…_ssp370_RH_dt3600` | `20260915_…_ssp585_RH_dt3600` |
| DF | `20260915_…_ssp119_DF_dt3600` | `20260915_…_ssp245_DF_dt3600` | `20260911_…_ssp370_DF_dt3600` | `20260915_…_ssp585_DF_dt3600` |

Transient 1850–2023: `20260911_seus_halfdeg_transient_dt3600`.
`…` = `seus_halfdeg_future`. SSP3-7.0 management cases carry the 20260911
date prefix; the other SSPs' management cases carry 20260915.

### 4 km

| | SSP1-1.9 | SSP2-4.5 | SSP3-7.0 | SSP5-8.5 |
|---|---|---|---|---|
| Default | `20260917_seus_4km_fut_ssp119` | `20260917_seus_4km_fut_ssp245` | `20260917_seus_4km_fut_ssp370` | `20260917_seus_4km_fut_ssp585` |
| RF | `20260915_seus_4km_fut_ssp119_RF` | `20260915_seus_4km_fut_ssp245_RF` | `20260917_seus_4km_fut_ssp370_RF` | `20260915_seus_4km_fut_ssp585_RF` |
| RH | `20260915_seus_4km_fut_ssp119_RH` | `20260915_seus_4km_fut_ssp245_RH` | `20260917_seus_4km_fut_ssp370_RH` | `20260915_seus_4km_fut_ssp585_RH` |
| DF | `20260915_seus_4km_fut_ssp119_DF` | `20260915_seus_4km_fut_ssp245_DF` | `20260917_seus_4km_fut_ssp370_DF` | `20260915_seus_4km_fut_ssp585_DF` |

Transient 1850–2023: `20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC`.

The full 4 SSP × 4 scenario design exists at both resolutions, so management
effects need not be restricted to SSP3-7.0.

## 2. What is identical across resolutions

| Item | Value (both resolutions) | How verified |
|---|---|---|
| Parameter file | `clm_params_SEUS_c260712.nc`, md5 `6b5a2ee2…`; the 0.5° 20260911 cases point to copies named `clm_params.nc` with the **same md5** | md5sum of all three paths |
| crit_dayl_stress | 36000 s (treated as 38000 s for analysis, decision 2) | paramfile |
| Timestep | ATM_NCPL = LND_NCPL = 24 (dt = 3600 s) | env_run.xml |
| Future start | 2024-01-01 from each resolution's own transient `elm.r.2024-01-01` | `finidat` |
| CO2 | `fco2_datm_<ssp>_1765-2500_c260818.nc` (same file per SSP); transient `fco2_datm_rcp4.5_…_c130312.nc` | lnd_in |
| N deposition | same file per SSP (1.9×2.5; ssp119 c260818, ssp245 c240903, ssp370 c220614, ssp585 c190103) | lnd_in |
| Aerosol deposition | `aerosoldep_rcp4.5_monthly_1849-2104_1.9x2.5_c100402.nc` | lnd_in |
| Lightning | `clmforc.Li_2012_climo1995-2011.T62.lnfm_Total` — a 1995–2011 **climatology**, no future change | lnd_in |
| Scenario land use | 0.5° files are area-weighted aggregates of the 4 km files (`SEUS_halfdeg_source_landuse` attribute); historical from the same `smoothHARV` file | file attributes |
| Model source | all executables compiled from the E3SM tree at HEAD `17efedae5f` (see §4) | build/exe dates vs reflog |

## 3. What differs between resolutions (configuration, not grid spacing)

| Item | 0.5° | 4 km | Consequence |
|---|---|---|---|
| Meteorology | `era5-daymet-fut-halfdeg`: TESSFA2 aggregated to 0.5° (`SEUS_halfdeg/data/processed/cpl_bypass_0p5deg_*`) | `era5-daymet-fut`: TESSFA2 native | Intended difference; aggregation method is part of the resolution effect |
| Surface data | `surfdata_SEUS_0_5deg_simyr1850.nc`, aggregated from the 4 km file (`build_surfdata_0p5deg.py`, 2026-08-20) | `surfdata_UpdatedsoilP_SEUS_1_24deg_simyr1850_c260712.nc` | Intended |
| HDM (population density, fire) | native `…hdm_0.5x0.5_AVHRR_simyr1850-2100_c240906.nc` | `elmforc.Li_hdm_1_24x1_24_bilinear_SEUS_…` (bilinear from 0.5°) | 4 km fire ignition/suppression has 0.5° effective resolution plus bilinear artifacts (the circular blobs, decision 3). Both are the SSP2 HDM for every SSP |
| Spin-up chain | `20260911_seus_halfdeg_{ad,final}_spinup_dt3600` | `20260910_…_30n_…_ad_spinup` → `20260911_…_20n_…_final_spinup` | Separate spin-ups; initial 2024 states differ by more than aggregation. Audit before calling a stock difference a grid effect |

Implication for the paper: native 0.5° vs 4 km is a comparison of two model
configurations. The primary resolution comparisons therefore use
**4 km aggregated to 0.5°** (same simulation) and the **downscaled 0.5°** field;
native 0.5° is secondary (blueprint decision framing).

## 4. Code-version labels are misleading — do not quote them

The `git_version` global attribute in the history files differs by group:
0.5° transient `94da735f76`, 0.5° futures `45d413e7aa`, 4 km transient
`17efedae5f`, 4 km futures `d2f7f285cc` (an unrelated upstream commit dated
2026-05-18). It equals each case's `MODEL_VERSION` in `env_case.xml`, which is
recorded when a case is created and **inherited by `create_clone`**. It is
not the source the executable was compiled from.

Evidence that all runs used the same source:
- The shared tree's last checkout was 2026-09-10 12:30; HEAD is `17efedae5f`
  (2026-09-10 12:59), and `components/elm` has no uncommitted changes.
- All executables are newer: 0.5° transient/futures built 2026-09-11 23:37–
  23:44 and 2026-09-15 22:09; the 4 km executable built 2026-09-14 03:10.
- All 16 4 km futures use the 4 km transient's EXEROOT; the transient ran
  2026-09-14 08:20 → 2026-09-17 07:01 with that same executable (the 9/17
  build logs are no-op keepexe builds; the exe timestamp is unchanged).
- Between `94da735f76` and `17efedae5f` the only model-source change is
  `components/elm/src/cpl/lnd_import_export.F90` (+31 lines, the cpl_bypass
  tindex fixes).

For Methods, cite `17efedae5f` (private fork `zzw0034/E3SM-pathfinder`) as the
model version, and state this inference.

## 5. Land-use file rewrites during the runs (checked, harmless)

The 4 km future land-use files were rewritten on 2026-09-05 (4 Default +
SSP3-7.0 DF/RH) and 2026-09-20 (other SSPs' DF/RH, plus the shared RF file),
after the 0.5° aggregation (2026-08-28). Cause: the float32→float64
`PCT_NAT_PFT` sum fix (ELM_Futu_landuseInput `BLOCKER_pct_nat_pft_sum.md`,
commits `9de4236`, `5d75f2f`). The sum error changed from ~5.6e-8 to ~7e-16.
The 0.5° aggregates were already clean. This is a precision correction, not
a land-use change, so 0.5° and 4 km scenario land use still match. The RF
rewrite was recorded as equivalent.

## 6. Other cohorts — not the paper cohort

| Cohort | Cases | Status (2026-09-23) | Role |
|---|---|---|---|
| crit_dayl_stress = 38000 s, 0.5° | `20260922_seus_halfdeg_future_ssp{119,245,370,585}{,_DF}_cds38000_dt3600` | complete | Expected size of a later full rerun (decision 2) |
| crit_dayl_stress = 38000 s, 4 km | `20260922_seus_4km_fut_ssp{119,245,370,585}{,_DF}_cds38000` | running (watchdog) | Same; no RF/RH exist at 38000 s |
| Legacy 4 km | 20260908 family, archived in `/projects/…/e3sm_run/20260901_before_seus_rerun` | complete | Void for the paper; used only by `rerun_comparison/` |

## 7. Storage and access

Per-case `run/` size: 0.5° future 12 GB, 0.5° transient 25 GB, 4 km future
1.6 TB, 4 km transient 3.3 TB — about 29 TB for the 4 km cohort, all on
scratch (90-day atime purge). Build compact extracted caches (decade means,
annual domain series, PFT-level fields needed for the downscaled field) early,
and keep them on proj-shared. Read h0/h1 only through Slurm, with
`time_bounds` day weighting.

## 8. Still to verify before Methods is written

1. Whether the two spin-up chains used the same spin-up length/protocol and
   equivalent convergence (the 0.5° chain: memory note of 440 yr, 0.58%/century).
2. The aggregation method for 0.5° meteorology (area-weighted mean of the
   144 sub-cells assumed; confirm in `SEUS_halfdeg/docs/DESIGN_DECISIONS.md`).
3. That the 4 km bilinear HDM file was derived from the same 0.5° Li SSP2
   product the 0.5° runs read (its name suggests so), so HDM differs between
   resolutions only by interpolation.
