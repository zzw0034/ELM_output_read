# Analysis process notes — SEUS high-resolution ELM manuscript

Updated: 2026-09-24. This is a working map of data, code, and provenance,
not a claim that the analyses below have been rerun. Paths and case availability
on Pathfinder must be rechecked when a new job is prepared.

## 1. Which simulations supply the analysis?

- Local manuscript workspace:
  `/Users/zw5/ORNL_workplace/pathfinder/ELM_output_read/analyses/paper_carbon_offset/`.
  Its declared Pathfinder mirror is
  `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/`.
- Pathfinder raw-output root:
  `/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/`.
  A case's history is under `<root>/<case>/run/`, with files such as
  `<case>.elm.h0.*.nc` (gridcell output) and `<case>.elm.h1.*.nc` (PFT output).
- **Current selection:** use the 38 exact directory names in
  [RESULTS_SUMMARY.md, §0](RESULTS_SUMMARY.md). This is 32 future cases
  (4 SSPs × Default/RF/RH/DF × 2 resolutions) plus 6 spin-up/transient
  directories. Default and DF use the 16 `cds38000` future directories;
  RF and RH use the 16 directories without that suffix. Spin-up and transient
  directories also lack that suffix. The 16 older Default/DF future directories
  are present but excluded.
- Historical/transient runs cover 1850–2023; future runs cover 2024–2100
  according to the earlier [case audit](CASE_MATRIX.md). That audit verified
  the older 34-case selection, **not** the completeness and configuration of
  every newly selected `cds38000` run. The 2026-09-24 check established
  directory existence only. Check actual h0/h1 years, record counts and
  metadata before extracting the mixed 38-case selection.
- CIME case/configuration root recorded by the audit:
  `/projects/hpcl-cli185/proj-shared/zw5/e3sm_cases/<case>/`.
  Check each selected case's `lnd_in`, `env_run.xml`, `env_case.xml`,
  parameter file, restart/finidat, input file paths, and executable provenance
  before treating a scenario difference as a controlled management effect.

**Important mapping gap:** [CASE_MATRIX.md](CASE_MATRIX.md) and
[code/common.py](code/common.py) still point Default/DF to their earlier
non-`cds38000` future directories. The current user-approved selection is
recorded in RESULTS_SUMMARY §0, but has **not** been implemented in the case
loader. Do not run a manuscript script or reuse a cache under the assumption
that `PAPER_COHORT=rerun_20260910` already selects all 38 directories.

## 2. Model inputs and where to establish their provenance

| Input | Current evidence / location | Detail to preserve |
|---|---|---|
| Meteorology | [CASE_MATRIX.md, §3](CASE_MATRIX.md): 4 km `era5-daymet-fut` / TESSFA2 native; 0.5° `era5-daymet-fut-halfdeg`, aggregated TESSFA2 files under `SEUS_halfdeg/data/processed/cpl_bypass_0p5deg_*` | Exact file and aggregation method from each selected case's `lnd_in` and forcing-workflow documentation |
| Surface data and soils/PFTs | Audit records `surfdata_UpdatedsoilP_SEUS_1_24deg_simyr1850_c260712.nc` at 4 km and `surfdata_SEUS_0_5deg_simyr1850.nc` at 0.5° | Verify paths and versions for the selected runs; the 0.5° file is an aggregation of the 4 km source |
| Historical/future land use and harvest | Case `lnd_in`; scenario definitions in `ELM_Futu_landuseInput/harvest_scenarios/HARVEST_SCENARIOS.md` in the workspace | Record the exact land-use files and how RF, RH, DF differ from Default; RF combines restoration with broader protection/zero harvest |
| CO₂, nitrogen and aerosol deposition | File names and SSP mapping are recorded in [CASE_MATRIX.md, §2](CASE_MATRIX.md); exact active paths belong to each `lnd_in` | Do not infer that every driver varies at 4 km; deposition and CO₂ have coarser effective support |
| Fire forcing | Case `lnd_in` and [CASE_MATRIX.md, §3](CASE_MATRIX.md): HDM population-density input is coarse and interpolated for 4 km; lightning is a 1995–2011 climatology | HDM contributes the circular structures in 4 km fire maps; report the fire component and repeat selection analyses without it |
| ELM source and spin-up | [CASE_MATRIX.md, §§3–4](CASE_MATRIX.md) records differing spin-up chains and an inferred model-source HEAD `17efedae5f` for the earlier cohort | Reverify executable and restart provenance for the `cds38000` cases before using that inference in Methods |

The root path above is Lustre scratch and is purgeable. These source
locations are pointers, not a durable backup. Do not copy large NetCDF
outputs into this Git repository. Put durable compact extracts in an
approved persistent location and record their source case and code commit.

## 3. Observation-based data and historical comparison

The existing observational panel is implemented in
[plot_biomass_soc_panel.py](../carbon_offset_poster/codes/plot_biomass_soc_panel.py).
It is illustrative, not yet the quantitative Figure 1 evaluation.

| Field | File used by that script | Processing and status |
|---|---|---|
| ESA-CCI aboveground biomass | `/Users/zw5/ORNL_workplace/wildfires/ELM_results4CCSImidmeet/otherdata00/biomass/ESACCI/biomass_masked_kgm2.nc` | **Superseded for the paper by v7.0 (§3.1).** Checked 2026-09-24: this is ESA-CCI v5.01 coarsened to 0.04° by ILAMB; its 8 bands are 2010 and **2015–2021** (time axis), so the script's "2014–2020" labels are off by one year; values are **dry biomass** ×0.1 (kg m⁻²), not carbon, although the poster labels them kg C m⁻². |
| SoilGrids SOC | `/Users/zw5/ORNL_workplace/wildfires/ELM_results4CCSImidmeet/otherdata00/soc/soilgrids/` | Script reads `ocd_0-5cm_mean.tif`, `ocd_5-15cm_mean.tif`, `ocd_15-30cm_mean.tif`; converts concentration using its documented factor and integrates the three layer thicknesses to 0–30 cm. SoilGrids is not an annual 2014–2020 observation series. |
| ELM comparison extracts | `analyses/carbon_offset_poster/_cache/ELM_biomass_soc_0_30cm_4km.nc` and `ELM_biomass_soc_0_30cm_0.5deg.nc` | Generated by [extract_biomass_soc.py](../carbon_offset_poster/codes/extract_biomass_soc.py) from historical h0 files, nominally 2014–2020. Confirm the embedded `case`, `run_dir`, units and years before reuse with the selected cohort. |

These six local input/cache files were present in the 2026-09-24 local
path check; that check did not verify their scientific provenance or contents.
The ELM extractor uses `TOTVEGC_ABG` for aboveground carbon. It derives
0–30 cm SOC from depth-integrated `SOIL1C_vr` through `SOIL4C_vr`, with
layer overlaps calculated from `DZSOI`, then saves both in kg C m⁻².
The poster script uses the aboveground-carbon NaN mask for extracted SOC
because inactive cells otherwise appear as zero SOC.

Before claiming observational skill, align support, years, units, depth,
forest/land masks and area weights. Evaluate common 0.5° support and
within-cell anomalies separately. GEDI/FIA-based AGB and gSSURGO SOC are
**planned independent checks**, not sources currently wired into these
scripts. See [the Figure 1 plan](manuscript_figure_results_discussion.md).

### 3.1 ESA CCI Biomass v7.0 AGB — Figure 1 primary AGB observation (2026-09-24)

**Stored file (Pathfinder, persistent):**
`/projects/hpcl-cli185/proj-shared/zw5/obs_data/biomass/ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0_SEUS_lat24-37.5_lon-95--74.nc`
(40.6 MB, md5 `d6d6330035e643b2ac9dcdeeafdbab08`), with a provenance
`README.md` in the same directory.

**Product, citation and licence**

- Product: ESA Biomass Climate Change Initiative (Biomass_cci), global forest
  above-ground biomass, **version 7.0**, 1 km aggregated product
  (`ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0.nc`, global 2.98 GB, created
  2025-12-19). Supersedes the ILAMB-processed v5.01 file above.
- Citation: Santoro, M.; Cartus, O. (2026): ESA Biomass Climate Change
  Initiative (Biomass_cci): Global datasets of forest above-ground biomass for
  the years 2005-2012 and 2015-2024, v7.0. NERC EDS Centre for Environmental
  Data Analysis, 21 May 2026. doi:10.5285/6429d1aafe1e43b9b414e4a5a7f8b903
- Catalogue: https://catalogue.ceda.ac.uk/uuid/6429d1aafe1e43b9b414e4a5a7f8b903
- Source file URL:
  https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0.nc
- Licence: open access; terms in
  https://artefacts.ceda.ac.uk/licences/specific_licences/esacci_biomass_terms_and_conditions_v2.pdf
  (cite the dataset as above).

**Variable definition (CEDA catalogue abstract).** The AGB data products
consist of two global layers:

> 1) above ground biomass (AGB, unit: tons/ha i.e., Mg/ha) (raster dataset).
> This is defined as the mass, expressed as oven-dry weight of the woody parts
> (stem, bark, branches and twigs) of all living trees excluding stump and
> roots per unit area
>
> 2) per-pixel estimates of above-ground biomass uncertainty expressed as the
> standard deviation in Mg/ha (raster dataset)

The netCDF attributes say only "Above-ground biomass", Mg/ha; the
dry-weight/woody-parts definition is stated only in the catalogue abstract, so
cite the catalogue record in Methods. Foliage is **not** included.

**Subset, indices and years**

- Box = the nominal SEUS 1/24° ELM grid (`make_scrip_1_24_deg.py`), cell
  edges lat 24.0–37.5, lon −95.0 to −74.0. The source 0.01° grid
  (GeoTransform −180, 0.01, 90, −0.01) has pixel edges exactly on these
  bounds, so the subset is index-exact: **lon[8500:10600]** (centres
  −94.995…−74.005, 2100 columns) and **lat[5250:6600]** (centres
  37.495…24.005, 1350 rows, north→south).
- **All 18 epochs**: 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2015,
  2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 (`time` = 1 January of
  the map year, days since 1990-01-01).
- Variables `agb` and `agb_sd` copied unchanged (int16, Mg/ha,
  `_FillValue` −32768).
- Fetched by HTTP byte-range read (no full-file download) with
  [code/obs_fetch_esacci_agb_v7_seus.py](code/obs_fetch_esacci_agb_v7_seus.py)
  (commit `4511bf9`, script md5 `f26be28b3e7d9e80448c4a3ec2b30f46`), run on
  the Pathfinder login node as a network-only transfer. Verification: random
  50×50 blocks in three epochs are identical to the CEDA source.

**Processing conventions (decided 2026-09-24)**

- **Carbon fraction 0.47**: AGB carbon = 0.47 × dry AGB, i.e.
  kg C m⁻² = 0.047 × (Mg ha⁻¹). Apply it once, in the analysis code, not to
  the stored file.
- Ocean and non-forest pixels are stored as **0, not missing** (53% of the
  box is 0 in 2020). Take the land mask and land-area denominator from the ELM
  domain/`landfrac`, never from this file; otherwise coastal 4 km cells
  average ocean in as zero biomass.
- 0.5° cells nest exactly (50×50 pixels); 1/24° cells do not (≈4.17 pixels
  per side) and need area-overlap weights.
- Still open: whether to subtract `LEAFC` from ELM `TOTVEGC_ABG` to match the
  woody-only definition, the averaging window, and the remaining Figure 1
  decisions.

## 4. Script and product locations

| Purpose | Location / entry point | Current state |
|---|---|---|
| Main manuscript analysis code and shared case loader | [code/](code/README.md), especially [code/common.py](code/common.py) | Legacy figure scripts; case mapping must be updated before selected-cohort reruns |
| Pathfinder batch wrapper | [code/submit_py.sbatch](code/submit_py.sbatch) | Runs a specified Python script from the manuscript analysis root; resources and remote paths must be checked before use |
| Historical AGB/SOC extraction | [poster extraction script](../carbon_offset_poster/codes/extract_biomass_soc.py) and its [batch wrapper](../carbon_offset_poster/codes/submit_py.sbatch) | Separate poster workflow; output directory is a command argument |
| Observational comparison plot | [poster panel script](../carbon_offset_poster/codes/plot_biomass_soc_panel.py) | Local plotting from extracted ELM cache and local observation files |
| Generated manuscript plots | `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/figures/<PAPER_COHORT>/` | Intended path in `code/common.py`; present local `figures/legacy/` PNGs are old-cohort figures and not current evidence |
| Intermediate numerical cache | `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/_cache/<PAPER_COHORT>/` | Script cache keys lack a complete source-version signature; never reuse across case-map changes without explicit validation |
| Slurm logs | `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/logs/` | Generated job output; do not commit |

Current scripts and their proposed figure roles are listed in
[code/README.md](code/README.md). In particular, the old `fig05` script
plots vulnerability quadrants; it does **not** implement the proposed
equal-area 20%/30% priority-area experiment. Quantitative AGB/SOC skill and
within-0.5°-cell tests likewise require new analysis code.

## 5. Accounting and analysis conventions to record with each result

- Record the source case pair, SSP, resolution, variable, years, spatial
  mask/eligible area, area weights, code commit, cache identity, and units.
- Report RF − Default and RH − Default as management-related stock
  differences; report Default − DF as an idealized avoided-loss bound.
  Compare pairs only within the same SSP and resolution. Because the
  selected Default/DF and RF/RH come from different run batches, check
  actual parameter, restart and forcing compatibility; otherwise the
  RF/RH difference is not a clean one-factor management effect.
- Use `TOTECOSYSC` for the primary stock outcome. In the ELM source
  examined for the blueprint it includes vegetation, coarse woody debris,
  litter, soil and product carbon. Distinguish that boundary from
  aboveground biomass, in-situ ecosystem carbon, and NBP flux. Close pool
  sums before reporting contribution percentages.
- Weight monthly h0/h1 values using `time_bounds` where appropriate,
  check complete years, mask inactive land, and use cell area × land
  fraction for regional totals and equal-area selection. Do not use cell
  counts as a proxy for physical area.
- Fire loss is already reflected in the model's net carbon outcome.
  Do not subtract it a second time in a risk screen. Separate
  `PFT_FIRE_CLOSS` from complete column fire loss; neither fire-loss
  intensity nor a vulnerability rank is a project reversal probability.

## 6. Safe next steps

1. Verify the 38 selected directories' h0/h1 files and actual
   configuration, especially the `cds38000` Default/DF versus RF/RH
   comparison.
2. Update the case-map code and [CASE_MATRIX.md](CASE_MATRIX.md) together
   after that audit; invalidate incompatible caches.
3. Create small, provenance-tagged extracts and rerun the five-figure
   analysis plan, starting with the historical observational evaluation.
4. Keep remote inspection read-only unless transfer or Slurm submission
   has been explicitly approved under the workspace AGENTS.md. No remote
   files or jobs were changed to prepare this note.
