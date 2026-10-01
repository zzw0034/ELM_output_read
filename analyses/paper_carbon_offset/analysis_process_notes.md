# Analysis process notes — SEUS high-resolution ELM manuscript

Updated: 2026-09-24. This is a working map of data, code, and provenance,
not a claim that the analyses below have been rerun. Paths and case availability
on Pathfinder must be rechecked when a new job is prepared.

## 1. Which simulations supply the analysis?

- Local manuscript workspace:
  `/Users/zw5/ORNL_workplace/pathfinder/ELM_output_read/analyses/paper_carbon_offset/`.
  Its declared Pathfinder mirror (since 2026-10-01) is the persistent
  `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/`, laid out
  like this folder (`code/`, `figures/`, `_cache/`, `logs/`, docs). It
  replaced `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/`
  (the original flat copy, kept unchanged as a backup with a `README.md`
  added 2026-10-01 that points here and lists its unique contents: legacy
  caches and logs; scratch is purgeable and its project quota was exceeded
  on 2026-09-29) and absorbed
  `/projects/hpcl-cli185/proj-shared/zw5/ELM_output_read_extracts/paper_carbon_offset/`
  (its `obs_compare/` is now `_cache/obs_compare/`, `logs/` unchanged).
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
scripts. See the Figure 1 plan, [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md) Methods D6.

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
  [code/figure1/obs_fetch_esacci_agb_v7_seus.py](code/figure1/obs_fetch_esacci_agb_v7_seus.py)
  (commit `4511bf9`, script md5 `f26be28b3e7d9e80448c4a3ec2b30f46`), run on
  the Pathfinder login node as a network-only transfer. Verification: random
  50×50 blocks in three epochs are identical to the CEDA source.

**How the data were downloaded, and how to reuse the script**

- **Script:** `obs_fetch_esacci_agb_v7_seus.py`, md5
  `f26be28b3e7d9e80448c4a3ec2b30f46` in all copies:
  - Git (authoritative): [code/figure1/obs_fetch_esacci_agb_v7_seus.py](code/figure1/obs_fetch_esacci_agb_v7_seus.py)
    (first committed as `code/obs_fetch_esacci_agb_v7_seus.py` in `4511bf9`);
  - Pathfinder: `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/code/figure1/obs_fetch_esacci_agb_v7_seus.py`.
- **Method:** no login and no full download. netCDF-C opens the CEDA URL with
  `#mode=bytes`, i.e. HTTP range requests over HTTPS, and only the chunks
  covering the box are transferred (the global file is chunked 1 epoch ×
  1500 × 3000 pixels, so the SEUS box needs 4 chunks per epoch). The script
  (1) asserts the subset's centre coordinates, (2) writes coordinates,
  bounds and time, (3) copies `agb` and `agb_sd` epoch by epoch, unchanged,
  with retries, (4) copies the global attributes and adds `subset_source_url`,
  `subset_index`, `subset_epochs`, `subset_note` and a `history` entry with
  the script md5, and (5) writes to `<name>.part` and renames at the end. It
  refuses to overwrite an existing output.
- **Environment:** Pathfinder's login node can reach `dap.ceda.ac.uk` over
  HTTPS (the compute nodes were not tested). The Python is
  `/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python`
  (netCDF4 1.7.4, libnetcdf 4.10.0, which supports `#mode=bytes`). It is
  network-bound and light (one epoch, ~6 MB per variable, in memory; the
  2026-09-24 run took about a minute for 40 MB), so the login node is
  acceptable; summarize the command and get approval before running, per
  AGENTS.md.
- **Command used on 2026-09-24** (script streamed from the Mac; arguments are
  the output directory and the script md5 to record):

  ```bash
  ssh pathfinder "/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python - /projects/hpcl-cli185/proj-shared/zw5/obs_data/biomass f26be28b3e7d9e80448c4a3ec2b30f46" < code/obs_fetch_esacci_agb_v7_seus.py
  ```

  Equivalent today, run from the paper's remote root on Pathfinder:

  ```bash
  cd /projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset && /projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python code/figure1/obs_fetch_esacci_agb_v7_seus.py <out_dir> $(md5sum code/figure1/obs_fetch_esacci_agb_v7_seus.py | cut -d' ' -f1)
  ```

- **Look before fetching:** `ncdump -h "<URL>#mode=bytes"` reads only the
  header (dimensions, variables, time axis, grid); this is how the 18 epochs
  and the 0.01° grid were confirmed. `curl -s "https://data.ceda.ac.uk/<dir>?json"`
  lists a CEDA directory with file sizes.
- **Adapting it** (all settings are constants at the top of the script):
  - *Another box:* on this 0.01° global grid, `lon index = (lon_edge + 180) / 0.01`
    and `lat index = (90 − lat_edge) / 0.01` (rows run north→south, so the
    slice starts at the north edge); e.g. lon −95/−74 → 8500/10600 and
    lat 37.5/24 → 5250/6600, the slices used here. Set
    `LON_SLICE` / `LAT_SLICE` (end exclusive), the centre-coordinate
    assertions in `main()` and `OUT_NAME`. Choose edges on multiples of
    0.01° to keep the subset index-exact.
  - *Another version or resolution* (e.g. a later CCI release, or the 10 km
    file): change `URL` and `OUT_NAME`, read the header first, and recompute
    the slices if the grid step differs.
  - *Fewer epochs or variables:* edit `DATA_VARS` or the epoch loop; by
    default all epochs and `agb` + `agb_sd` are copied.
- **After a new fetch:** spot-check blocks against the source, record the
  output path, size and md5 here and in a `README.md` beside the data, and
  commit the script version that ran.

**Processing conventions (2026-09-24; carbon fraction changed 2026-09-29)**

- **Carbon fraction 0.50** (decided 2026-09-29, replacing the 0.47 chosen on
  2026-09-24): AGB carbon = 0.50 × dry AGB, i.e.
  kg C m⁻² = 0.05 × (Mg ha⁻¹). Apply it once, in the analysis code, not to
  the stored file. Reason: 0.47 is the IPCC 2006 cross-biome default, whereas
  IPCC 2006 gives about 0.48 for temperate broadleaf and 0.51 for temperate
  conifer wood, so the southeastern pine/hardwood mix is closer to
  0.49–0.50; 0.50 is also the long-standing convention. Report sensitivity
  over 0.47–0.51 (about ±4%). Values quoted from memory of IPCC 2006
  Table 4.3; confirm against the table before citing.
- A carbon fraction cannot close the ELM–ESA mean gap: matching the 4 km
  means would need ≈ 0.60, outside the plausible 0.44–0.55 range (§3.2).
- Ocean and non-forest pixels are stored as **0, not missing** (53% of the
  box is 0 in 2020). Take the land mask and land-area denominator from the ELM
  domain/`landfrac`, never from this file; otherwise coastal 4 km cells
  average ocean in as zero biomass.
- 0.5° cells nest exactly (50×50 pixels); 1/24° cells do not (≈4.17 pixels
  per side) and need area-overlap weights.
- Still open: whether to subtract `LEAFC` from ELM `TOTVEGC_ABG` to match the
  woody-only definition, the averaging window, and the remaining Figure 1
  decisions.

### 3.2 ESA-matched ELM 4 km quantity — first visual comparison (2026-09-29)

- **Quantity:** tree-PFT stem carbon, Σ over itype 1–8 of
  (LIVESTEMC + DEADSTEMC) × `pfts1d_wtgcell`, per unit gridcell land area;
  each year a day-weighted annual mean of the monthly h1 records (annual mean
  stock chosen over the December value). Shrub stems (itype 9–11) are stored
  separately; leaves and coarse roots excluded.
- **Source:** 4 km transient `20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC`
  h1, the 17 ESA epochs inside 1850–2023 (2005–2012, 2015–2023).
- **Extract:** `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/_cache/obs_compare/elm4km_tree_stemc_2005-2023.npz`
  (13.9 MB, md5 `7027ddaa5ef29f318796a9243f45cab7`; per-year `tree_stemc`,
  `shrub_stemc`, `tree_frac`, `veg_frac`, plus lat/lon/area/landfrac and
  provenance strings), made by
  [code/figure1/extract_elm_4km_tree_stemc.py](code/figure1/extract_elm_4km_tree_stemc.py),
  Slurm job 596693 (serial, 47 s). It is on proj-shared because the scratch
  project quota 55528 was over its soft limit with the grace period expired
  (239.6 T / 200 T), which made jobs 596645, 596680 and 596686 fail at the
  write step.
- **First-look figures** (ELM alone; ELM next to ESA on native grids, no
  common mask) were made with
  [code/figure1/plot_elm_vs_esacci_agb.py](code/figure1/plot_elm_vs_esacci_agb.py),
  as was the ESA-only mean map with
  [code/figure1/plot_obs_esacci_agb_v7_mean.py](code/figure1/plot_obs_esacci_agb_v7_mean.py).
  Their PNGs were deleted on 2026-10-01 at the user's request (the scripts
  regenerate them); Figure 1 keeps only the three-way and four-panel maps
  below.
- **0.5° counterpart:** the same script on `20260911_seus_halfdeg_transient_dt3600`,
  job 596700 (5 s), →
  `.../obs_compare/elm0p5deg_tree_stemc_2005-2023.npz` (0.1 MB, md5
  `995137936fb60e9fdfed19efae71cab8`).
- **Three-way map** ([code/figure1/plot_agb_elm4km_esa4km_elm0p5.py](code/figure1/plot_agb_elm4km_esa4km_elm0p5.py),
  `--cf`, md5 `0640eab1eeb7db5a74f5bcc77808a841`): ELM 4 km | ESA aggregated to the ELM 1/24°
  grid (exact area-overlap weights, land pixels only) | ELM 0.5° **copied to
  the 4 km grid** (comparator A). Since 2026-10-01 everything, maps and
  statistics, is on the 4 km grid, and a cell is shown and scored only where
  ELM 4 km, ESA and the copied 0.5° value are all valid (n = 75 902; no cell
  lost to a missing 0.5° parent). The earlier version drew the native 0.5° grid
  and also scored 0.5° block means; those numbers are superseded. Output kept:
  `figures/figure1/agb_elm4km_esa4km_elm0p5_2005-2023_cf50.png` (the cf47
  variant was deleted 2026-10-01; rerun with `--cf 0.47` if needed).
- **First-look statistics, carbon fraction 0.50** (4 km cells, common
  support; area × landfrac weights for every metric including r; no final
  mask rules, no 30.833°N exclusion; not the D6 evaluation):

  | Comparison | Means (Mg C/ha) | Bias | RMSE | r |
  |---|---|---|---|---|
  | ELM 4 km vs ESA→4 km | 48.9 vs 40.8 | +8.1 | 18.0 | 0.79 |
  | ELM 0.5° copied vs ESA→4 km | 52.1 vs 40.8 | +11.3 | 23.4 | 0.61 |
  | ELM 0.5° copied vs ELM 4 km | 52.1 vs 48.9 | +3.2 | 15.7 | 0.80 |

  With 0.47 the ESA means are 38.3 and the biases +10.6 (ELM 4 km) and
  +13.8 (0.5° copied); r is unchanged. ELM is high mainly in the Ozark/Ouachita, Kentucky/Cumberland
  and Carolina coastal-plain regions; the southern Appalachian high and the
  Delta/Atchafalaya pattern agree.

### 3.3 All fields on the 4 km grid, with the 0.5° comparators A and B (2026-09-29)

- **Per-type extracts** (jobs 596726, 596727; the extractor now also writes
  `stemc_dens_by_type` and `frac_by_type` for tree itype 1–8, asserting
  Σ_t density × fraction = `tree_stemc` every year):
  `.../obs_compare/elm4km_tree_stemc_bytype_2005-2023.npz` (32.8 MB, md5
  `24fc2e2de47eaaf0fa369a09cad423b5`) and
  `.../obs_compare/elm0p5deg_tree_stemc_bytype_2005-2023.npz` (0.3 MB, md5
  `5c8da59fe4e0269cb5a630d93bfe21bd`).
- **Comparators on the 4 km grid**
  ([code/figure1/plot_agb_4km_comparators.py](code/figure1/plot_agb_4km_comparators.py)):
  A = the 0.5° run copied to its 144 children; B = Σ_t density_t(0.5° parent)
  × fraction_t(4 km cell), per year then averaged. B averaged back over each
  0.5° cell reproduces the 0.5° run exactly (max |d| 0.00 Mg C/ha), and no
  fallback density was needed. Figure:
  `figures/figure1/agb_4km_comparators_2005-2023_cf50.png`.
- **Preview statistics, carbon fraction 0.50** (4 km cells vs ESA→4 km):

  | Field | Mean vs ESA 40.8 | Bias | RMSE | r |
  |---|---|---|---|---|
  | C ELM 4 km | 48.9 | +8.1 | 18.0 | 0.79 |
  | A 0.5° copied | 52.1 | +11.3 | 23.4 | 0.61 |
  | B 0.5° downscaled | 52.1 | +11.3 | 20.1 | 0.78 |

  Within-0.5° anomalies (≥ 72/144 valid children; 525 coarse cells;
  ESA anomaly SD 15.6 Mg C/ha): B r 0.77, skill score 0.60, SD ratio 0.82;
  C r 0.76, skill score 0.54, SD ratio 0.96; A is 0 by construction.
  Excluding the 30.5–31.0°N row (498 cells): B r 0.78, SS 0.60, SD ratio
  0.82; C r 0.77, SS 0.55, SD ratio 0.97.
- **Metric definitions.** Within each eligible 0.5° cell the anomaly is
  x′ = x − Σ w x / Σ w over the same valid children for every field, with
  w = area × landfrac. Over all eligible fine cells: r = area-weighted
  Pearson correlation of model and ESA anomalies; SD ratio k = weighted RMS
  of model anomalies / that of ESA; skill score SS = 1 − Σ w (m′ − o′)² /
  Σ w o′², i.e. improvement over the flat field A. Because anomalies have
  zero weighted mean, SS = 2 r k − k² exactly (asserted in the script), so
  for a given r the best SS is r² at k = r: extra amplitude without better
  placement lowers SS, which is why C scores below B at almost equal r.
- **Reading (preview):** for AGB, almost all of the within-cell skill of
  the 4 km run is already obtained by putting 0.5° per-PFT densities on 4 km
  land cover (B ≥ C). Running ELM at 4 km adds within-cell amplitude (SD
  ratio 0.96 vs 0.82) but not skill. This matches the D6 expectation that
  AGB mostly measures land cover; the SOC test is where running at 4 km
  must show value. Not yet done: final masks, the observational ceiling,
  uncertainty (e.g. block bootstrap), and SOC.
- **Which code made which extract.** All four `obs_compare/*.npz` were made
  by `extract_elm_4km_tree_stemc.py` run on Pathfinder from the scratch
  mirror `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/code/`
  (flat layout there; locally the script is now in `code/figure1/`), via
  `code/submit_py.sbatch`, logs in
  `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/logs/`.
  The `_bytype` files (jobs 596726, 596727) come from the version now on
  Pathfinder (md5 `1fd2a9a95ffc5d0aff4017792cddb476`, commit `4a169f4`).
  The two files without `_bytype` (jobs 596693, 596700) come from the
  previous version (md5 `bba97d47f1ff411f0e2945f56f2297ee`, commit `76bc6f5`),
  which was overwritten on Pathfinder and survives only in Git. The
  plotting scripts never ran on Pathfinder. After the 2026-10-01
  reorganization the script (`code/figure1/`, md5
  `e91f200c9655defc73bd03bb15b33eb8`) differs from the `1fd2a9a9…` version
  only in the usage path in its docstring; the computation is unchanged.

### 3.4 SOC observations on the 4 km grid, ELM SOC 2000–2023, first comparison (2026-10-01)

Everything below lives on Pathfinder under
`/projects/hpcl-cli185/proj-shared/zw5/obs_data/SOC/` (observations, each
product in its own folder together with a copy of its script and a README) and
`.../paper_carbon_offset/_cache/obs_compare/` (ELM extracts). Scripts are
authoritative in Git at `code/figure1/`; the remote paper root is an rsync
mirror, not a git clone.

**Depths and ELM quantity (decided 2026-10-01, blueprint A5).** 0–30 cm and
0–100 cm, both drawn. ELM 0–30 cm = Σ_k overlap_k(0–0.30 m) ×
(SOIL1C_vr+SOIL2C_vr+SOIL3C_vr+SOIL4C_vr)_k; ELM 0–100 cm = the model's own
`TOTSOMC_1m`. In `ColumnDataType.F90` `TOTSOMC_1m` is the sum of the
`is_soil` decomposition pools only (litter `TOTLITC_1m` and CWD are separate)
integrated over layers fully above 1 m plus the share of the straddling
layer, i.e. the same overlap rule as the 0–30 cm integral. Check: the
extractor also integrates SOIL1–4C_vr to 1.00 m and the maximum difference to
`TOTSOMC_1m` is 0.0000 kg C m⁻² in all 24 years at both resolutions. Layer
bottoms (m): 0.0175, 0.0451, 0.0906, 0.1655, 0.2891, 0.4929, 0.8289, 1.3828;
0–30 cm takes 0.0109 m of layer 6, 0–100 cm takes 0.1711 m of layer 8 (uniform
density inside a layer assumed). `DZSOI` is written only to the first h0 file
of a continuous run segment; later files name it in the global attribute
`Time_constant_3Dvars_filename` (0.5°: the 1850 file; 4 km: the 1999 file),
which the extractor follows. Each year is a day-weighted mean of the 12 monthly
records; the figure uses the mean of the 24 annual means, 2000–2023.

| Item | Value |
|---|---|
| ELM 4 km | `20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC`, h0 2000–2023; `_cache/obs_compare/elm4km_soc_2000-2023.npz`, 19.3 MB, md5 `23b50fc594598b7e90b900b0238e5f9a`, job 602051 (85 s, 0.6 GB RSS) |
| ELM 0.5° | `20260911_seus_halfdeg_transient_dt3600`; `_cache/obs_compare/elm0p5deg_soc_2000-2023.npz`, md5 `1e7875faf4da431aba7ceb37815b75dd`, job 602050 (8 s) |
| Extractor | `code/figure1/extract_elm_soc.py`, md5 `b073596d521dba75193559f8fb4795dd`, commit `b20ef4e`; smoke tests 602048/602049 (year 2000) preceded the full runs |
| Mean SOC, land cells (area × landfrac) | 4 km: 7.5 (0–30), 12.6 (0–100); 0.5°: 7.7, 12.9 kg C m⁻²; the 4 km run rises 7.44 → 7.53 (0–30) from 2000 to 2023 |

**SoilGrids 2.0** (`obs_data/SOC/soilgrids/`). ISRIC `ocd` (organic carbon
density, mean, hg/m³ ×0.1 = kg/m³; coarse fragments already accounted for)
layers 0–5, 5–15, 15–30, 30–60, 60–100 cm, fetched through the ISRIC WCS 1.0.0
(`https://maps.isric.org/mapserv?map=/map/ocd.map`, format `GEOTIFF_INT16`) as
five 504 × 324 GeoTIFFs whose pixel edges are the ELM cell edges (box
−95…−74°E, 24…37.5°N). The exact request URLs, byte counts and md5 of each
tif are in `raw/provenance.json`; the five md5 were identical on the Mac and
on Pathfinder (reproducible). Layer boundaries coincide with the target depths
(0–30 = three layers, 0–100 = five), so there is no partial layer. A cell is
valid only where all layers used are valid (77 961 of 163 296; ocean is
nodata). Output `SOC_soilgrids_SEUS_1_24deg.nc`, md5
`41ce8d284683b4e74d1119ba68579726`, job 602046; area-weighted mean over valid
cells 6.60 (0–30) and 11.80 kg C m⁻² (0–100).
**Caveat — resampling is done by the server.** This is the poster's route
(`download_soilgrid.py`) with the request box and pixel counts set to the ELM
grid instead of 25–40°N × 100–74°W. It is not our own area-weighted aggregate
of the 250 m pixels (that alternative was offered and not chosen). A test on
layer 0–5 cm: requesting 4× the pixels (2016 × 1296) and block-averaging 4 × 4
reproduces the direct 504 × 324 request with RMSE 10.8 hg/m³ (≈3 % of the
mean), bias +0.1, r 0.989, whereas the best single 4 × 4 sub-pixel gives
RMSE ≥ 16.4 — so the server resamples by something close to averaging, not
nearest neighbour. Not repeated for the other layers.
Script `code/figure1/obs_soc_soilgrids_wcs_4km.py`, md5
`e50c6e1562cd476f12493317b88d025c`: `fetch` on the login node (network only,
~0.4 MB), `process` via Slurm.

**HWSD v1.2** (`obs_data/SOC/hwsd/`). The regridded HWSD v1.2 of the ORNL DAAC
(Wieder, Boehnert, Bonan and Langseth, 2014, doi:10.3334/ORNLDAAC/1247; 27
`.nc4` files at 0.05° = 3 arc-minute plus one CLM-grid file), from the
original HWSD v1.2 (FAO/IIASA/ISRIC/ISSCAS/JRC, 2012) regridded from 30
arc-second by ArcGIS. Used: `AWT_T_SOC.nc4` (`SUM_t_c_12`, topsoil 0–30 cm,
md5 `37184939fc5e1788afe2bae0b30f734d`) and `AWT_S_SOC.nc4` (`SUM_s_c_1`,
subsoil 30–100 cm, md5 `04815e129b1e53fab2ab6b7134b00e03`), kg C m⁻², missing
= −1. **Provenance gap:** these are the local copies from the earlier
`wildfires` project (file dates 2014-09-12, folder
`/Users/zw5/ORNL_workplace/wildfires/ELM_results4CCSImidmeet/otherdata00/soc/HWSD_1247/data/`),
copied to Pathfinder with scp. The ORNL DAAC download needs an Earthdata login
and was not repeated, and no direct download URL was verified in this
session; the local `guide/Online_Version_HWSD.html` only redirects to
`https://daac.ornl.gov/SOILS/guides/HWSD.html`; the documentation PDFs are in
`.../HWSD_1247/comp/`.
**Caveat — the source is coarser than the target.** 0.05° (3′) is coarser than
1/24° (2.5′), so each 4 km cell takes the exact area-overlap weighted mean of
the 0.05° cells it touches (valid cells only); this is a remap, not an
aggregation, and carries no 4 km information. 0–100 cm = topsoil + subsoil
where both are valid. The old `process_HWSD_1247.py` added the two files
without masking the −1 fill. Output `SOC_hwsd_SEUS_1_24deg.nc`, md5
`089510a149c832ce5f1aa759299a8e43`, job 602047 (also stores the valid share of
each cell; 1 033 cells have < 0.5); 79 658 valid cells; area-weighted mean
5.12 (0–30) and 10.39 kg C m⁻² (0–100), against 5.09 and 10.30 for the source
cells inside the box. Script `code/figure1/obs_soc_hwsd_v12_4km.py`, md5
`961118c6e6dbd58949d3c8a294ce4ce4`, commit `b20ef4e`. Minimum 0.00: some
cells carry no SOC in HWSD.

**Figures** (local, `figures/figure1/`, git-ignored; script
`code/figure1/plot_soc_elm4km_obs4km_elm0p5.py`, md5
`5128f4cee7d8f0a14974bbd2ac15f57e`, run from `_cache/obs_soc/` and
`_cache/obs_compare/` pulled with scp, md5 verified): one figure per product,
rows = 0–30 and 0–100 cm, columns ELM 4 km | observation on the 4 km grid |
ELM 0.5° **copied to the 4 km grid**. Everything, maps and statistics, is on
the 4 km grid (user requirement, 2026-10-01): each 0.5° cell is copied to its
12 × 12 children (comparator A of blueprint A4; SOC has no land-cover
downscaling B because all natural PFTs share one soil column). A 4 km cell is
shown and scored only if ELM 4 km, the observation and the copied 0.5° value
are all valid, so both models are scored on the same cells (no cell was lost
to a missing 0.5° parent; n = 75 672 for SoilGrids, 75 911 for HWSD). An
earlier version of this figure showed the native 0.5° grid and scored it at
0.5°; those numbers are superseded.
`soc_elm4km_soilgrids4km_elm0p5_2000-2023.png`,
`soc_elm4km_hwsd4km_elm0p5_2000-2023.png`. Colour scales are fixed and shared
by both products (0–12 and 0–24 kg C m⁻², extend max) with the continuous
`BrBG` colormap of the poster SOC panel (brown low, teal high; the midpoint
sits near the typical value). With a data-driven scale the HWSD wetland
hotspots stretched the scale and washed ELM out; hotspots now saturate.

A one-row companion, SOC 0–30 cm only, ELM 4 km | ELM 0.5° (copied to 4 km) |
SoilGrids | HWSD on the same 4 km cells (`figures/figure1/soc030_elm4km_elm0p5_soilgrids_hwsd_2000-2023.png`,
`code/figure1/plot_soc030_elm4km_elm0p5_soilgrids_hwsd.py`, md5
`3fba90e709a68da31183fdfd89eae192`; same BrBG 0–12 scale). A cell is shown only if all four
fields are valid (n = 75 671). It also annotates HWSD vs SoilGrids
(bias −1.6, RMSE 3.2, r +0.33 at 4 km cells), the two products' mutual
agreement, next to ELM's scores against each (ELM 4 km: +1.0/2.0/+0.13 vs
SoilGrids, +2.6/4.4/−0.20 vs HWSD).

**First-look statistics** (4 km cells, common support; area × landfrac
weights; mean of ELM 2000–2023; bias = ELM − obs; not the D6 evaluation):

| Product, depth | Mean ELM 4 km / obs | Bias | RMSE | r | Mean ELM 0.5° copied | Bias | RMSE | r |
|---|---|---|---|---|---|---|---|---|
| SoilGrids 0–30 | 7.50 / 6.49 | +1.0 | 2.0 | +0.13 | 7.70 | +1.2 | 2.1 | +0.14 |
| SoilGrids 0–100 | 12.64 / 11.32 | +1.3 | 4.7 | −0.23 | 12.90 | +1.6 | 4.8 | −0.24 |
| HWSD 0–30 | 7.49 / 4.93 | +2.6 | 4.4 | −0.20 | 7.69 | +2.8 | 4.5 | −0.26 |
| HWSD 0–100 | 12.62 / 9.91 | +2.7 | 8.7 | −0.26 | 12.88 | +3.0 | 8.9 | −0.31 |

ELM 0.5° (copied) vs ELM 4 km: bias +0.2 (0–30) and +0.3 (0–100), RMSE 0.8 and
1.3, r 0.83–0.85.

**Reading (preview).** ELM is higher than both products at both depths and
agrees poorly in space: r is between −0.31 and +0.14 for both runs. The 4 km
run has a 0.1–0.2 kg C m⁻² lower RMSE than the copied 0.5° run in all four
cases and a 0.2–0.3 smaller bias, but r differs by ≤ 0.06 and is not
consistently better (SoilGrids 0–30 cm: +0.13 vs +0.14), so there is no clear
sign that running at 4 km improves SOC against these products on the 4 km
cells. ELM's pattern is a north-high, south-low gradient with maxima in the
Appalachians and Ozark/Ouachita; both products have little gradient but
wetland/organic-soil hotspots (South Florida, Mississippi delta and
Louisiana, North Carolina coastal pocosins) that ELM, with one soil column and
no organic soils, cannot reproduce; it matches the South Florida deficit
already diagnosed in `carbon_offset_poster/codes/diagnose_south_fl_soc*.py`.
A test that the weak r is only the hotspots was **negative**: excluding the
cells above 12 (0–30) or 30 kg C m⁻² (0–100) in the observation (0.6–1.7 % of
cells) leaves Pearson +0.15 / −0.18 for SoilGrids and −0.28 / −0.39 for HWSD,
and rank correlation (Spearman) of +0.26 / +0.01 and −0.01 / −0.06, so the
disagreement is broad. Open before any claim: whether to mask or weight
organic-soil cells; within-0.5°-cell anomaly skill (D6 step 3; the only place
the 4 km run can show a SOC benefit, because coarse SOC has no downscaled
comparator); a second independent product (gSSURGO) as the observational
ceiling; and what the SoilGrids/HWSD disagreement with each other (HWSD is
4.9 vs 6.5 kg C m⁻² in 0–30 cm) implies for the evaluation.

### 3.5 Figure 2, historical regional series from the 4 km transient (2026-10-01)

The historical figure shows both resolutions, **4 km solid and 0.5° dashed**
(user request 2026-10-01). The per-scenario management figures will use the 4 km
runs only and show results, not a resolution comparison (user decision
2026-10-01; this reading of the two requests should be confirmed). Cases: 4 km
`20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC`, 0.5° `20260911_seus_halfdeg_transient_dt3600`,
h0/h1 1850–2023. Annual values are day-weighted means of the 12 monthly
records; domain totals = Σ field × area × landfrac over land cells (1.3562 Mkm²).

| Item | Value |
|---|---|
| Totals extractor | `code/figure2/extract_domain_totals.py` (TOTECOSYSC, TOTVEGC, TOTVEGC_ABG, CWDC, TOTLITC, TOTSOMC, GPP, NBP, WOOD_HARVESTC, LAND_USE_FLUX; product residual), md5 `5bdcbbfdd2cce2bf54d6e04b5da87418`, commit `c058c79`; job 602146 (18 min, 0.1 GB) → `_cache/figure2/transient_domain_totals_4km.npz`, md5 `951c09bc3e27bf8c348a02118bc26480` |
| Forest-area extractor | `code/figure2/extract_forest_area.py` (Σ pfts1d_wtgcell × area × landfrac by itype; tree = itype 1–8), md5 `e205186833aa36a531435b2b575083e6`; job 602148 (4 min) → `transient_forest_area_4km.npz`, md5 `aae3adb6569bfed08accc033f6c3c254` |
| Plot | `code/figure2/plot_historical_regional_series.py`, md5 `a2d504063c7c4da1ed5bc5ff46180eec` → `figures/figure2/hist_regional_series_1850-2023.png` (git-ignored) |
| 0.5° counterparts | same extractors; jobs 602147 (totals, md5 `6267909696638d15ca6dd6fb13f49748`) and 602149 (forest area, md5 `664fd8e2dd3590b22b3d24afbb23856c`), in the same `_cache/figure2/` |

First jobs 602135–602138 failed on purpose: the first record of a run starts one
model time step early (1850 file: time_bounds −1/24 d), which the extractors'
strict calendar-year assertion rejected; the tolerance is now < 1 day and each
use prints a note (effect on a day-weighted annual mean ≈ 0.01 %).

Results (4 km unless stated, 1850 → 2023): forest (tree-PFT) area 976 → 805 ×10³ km² (72 %
→ 59 % of land; minimum 783 in 1948); GPP 2.09 → 3.03 PgC/yr; SOC (TOTSOMC)
25.25 PgC in 1850, +0.87 PgC by 2023; NBP between −0.22 and +0.20 PgC/yr, mean
positive after ~1930 (2000–2023 mean +0.051 PgC/yr). The 0.5° run differs little in GPP (3.05) and NBP
(+0.049) but gains more SOC: +1.25 against +0.87 PgC; forest area is identical in the two runs because
the 0.5° land cover is the area-weighted aggregate of the 4 km one. Checks: the PFT area sums to the land area (ratio 1.0000
every year); the product residual TOTECOSYSC − (TOTVEGC+CWDC+TOTLITC+TOTSOMC)
grows from +0.03 to +0.83 PgC, so **TOTECOSYSC does include the product pools**
(the h0 long_name "excl product pools" is stale; consistent with
`ColumnDataType.F90` and blueprint D4); cumulative NBP 1850–2023 is −2.00 PgC
against a TOTECOSYSC change of −2.13 PgC (a 0.13 PgC, 6 % gap that is not yet
explained: annual-mean vs year-end stock, or the NBP definition at the product pool).

### 3.6 Figure 2, per-scenario management benefits from the ELM 4 km future runs (2026-10-01)

4 km only, results only (user decision 2026-10-01). 20 cases (4 SSPs × 5): the 36000 s Default,
RF and RH, and the `cds38000` Default and DF, named in `code/common.py` (`FOURKM["<SSP> cds38000"]`,
`["<SSP> DF cds38000"]`). Pairing (blueprint A2): RF − Default and RH − Default against the 36000 s
Default, **DF against the 38000 s Default**, written as Default − DF (positive = avoided loss).
Extractors as in §3.5 (`extract_domain_totals.py` md5 `5bdcbbfdd2cce2bf54d6e04b5da87418`,
`extract_forest_area.py` md5 `e205186833aa36a531435b2b575083e6`); 40 jobs, one per (case, script),
**Slurm jobs 602234–602273 on `serial`/`normal`, `-t 08:00:00`** (command-line overrides of
`code/submit_py.sbatch`), all COMPLETED, ≈ 19–35 min for the totals jobs and a few minutes for the forest
jobs. A first batch of the same 40 jobs, 602182–602224 on the dedicated partition `hpcl-cli185`, was
cancelled while running at the user's request (the dedicated partition was occupied) and wrote nothing.
Outputs `_cache/figure2/future_4km/<SSP>[_RF|_RH|_cds38000|_DF_cds38000]__{totals,forest}.npz` on
Pathfinder, copied to the same local path, all 40 md5 identical. Plot:
`code/figure2/plot_scenario_management_benefits.py`, md5 `289d4062ea1edeed3813eb2c6af2a207` →
`figures/figure2/management_benefits_<SSP>_4km.png` (one per SSP; rows cumulative NBP benefit and forest
area change, left RF and RH, right DF on its own axes).

Cumulative NBP benefit(t) = Σ_{y=2024..t} of the paired annual NBP difference; forest area is the
same-sign annual difference of the tree-PFT area. Results at 2100 (4 km):

| SSP | mgmt | cum. NBP benefit (PgC) | forest area change (10³ km²) | TOTECOSYSC difference (PgC) |
|---|---|---|---|---|
| SSP1-1.9 | RF / RH / DF | +3.73 / +0.98 / +11.22 | +87.5 / 0.0 / +859.7 | +3.62 / +0.94 / +11.02 |
| SSP2-4.5 | RF / RH / DF | +4.46 / +1.45 / +11.75 | +30.9 / 0.0 / +916.3 | +4.30 / +1.38 / +11.68 |
| SSP3-7.0 | RF / RH / DF | +5.21 / +1.00 / +10.85 | +173.8 / 0.0 / +773.3 | +5.03 / +0.95 / +10.67 |
| SSP5-8.5 | RF / RH / DF | +5.31 / +1.24 / +10.72 | +118.0 / 0.0 / +829.2 | +5.15 / +1.18 / +10.65 |

Things to know before interpreting:

- **The 2024 paired differences are not zero.** Management acts from the first simulated year: in 2024 the DF
  pair already differs by +5.8 to +6.2 PgC/yr of NBP and +805 to +815 ×10³ km² of forest (DF replaces nearly
  all forest at once), so about half of the 2100 DF benefit (≈ 6 of 11 PgC) accrues in the first year; RF adds
  forest gradually (+2 to +5 ×10³ km² in 2024, ≈ +160 by 2049 for SSP3-7.0). Blueprint D3's "exactly zero in
  2024" holds only for the 1 January 2024 restart state, not for the 2024 annual means.
- **Why the RF − Default forest-area curve falls after 2049.** RF is one shared policy prescription (not per SSP): forest is
  added linearly over 2024–2050 and then held fixed (947.2 ×10³ km² in all four SSPs, flat in 2051–2100), whereas the Default
  keeps changing (SSP2-4.5 +57 ×10³ km² between 2051 and 2100, SSP1-1.9 +20, SSP5-8.5 +14, SSP3-7.0 −11). The paired
  difference therefore shrinks once the Default catches up (SSP2-4.5: +91 in 2049, +31 in 2100); the RF forest itself does not
  shrink. `code/figure2/plot_scenario_management_forest_abs.py` (md5 `f2fe988e3a53a1bff2545fb355e8d98a`) draws the same figures with the
  absolute forest-area change of each run (`figures/figure2/management_benefits_forest_abs_<SSP>_4km.png`): (c) RF and the
  36000 s Default (RH has an identical forest area, asserted in the script), (d) DF (−805 ×10³ km² from 2024) and the 38000 s
  Default; the two Defaults have the same forest area, as expected since `crit_dayl_stress` does not change land cover.
- RH changes carbon but **not forest area** (difference exactly 0.0 in every year and SSP).
- The RF forest-area advantage peaks in 2049 and then shrinks in SSP2-4.5 (+91 → +31) and SSP5-8.5, because the
  Default's own forest area changes; it is a paired difference, not the RF forest area.
- **Closure:** the cumulative NBP benefit exceeds the TOTECOSYSC difference by 0.04–0.20 PgC (2–4 % of the
  benefit), always in the same direction; the historical series has a gap of the same sign (§3.5). Not yet
  explained (annual-mean vs year-end stock, or the NBP definition at the product pool).
- At 2100 DF ≈ 2 × RF ≈ 8–11 × RH in carbon, similar to the legacy ratio DF : RF : RH ≈ 10 : 5 : 1; DF is an
  idealized avoided-loss bound, not a policy estimate.

### 3.7 Figure 2, Default trajectories of the four SSPs, ELM 4 km (2026-10-01)

`code/figure2/plot_default_ssp_trajectories.py`, md5 `364cd4ca465f27a7e5ba99e636fbdf65`, from the extracts of §3.5 (history
2000–2023) and §3.6 (the four **36000 s Default** runs, 2024–2100; the Default paired with RF and RH):

- `figures/figure2/ssp_forest_area_change_2000-2100_4km.png`: tree-PFT area change since 2023 (805 ×10³ km²),
  four SSPs on one panel. At 2100: SSP1-1.9 +55, SSP2-4.5 +111, SSP3-7.0 −32, SSP5-8.5 +24 ×10³ km² (2050:
  +36, +53, −19, +9). Lines have kinks about every 5 years, probably the spacing of the land-use input (not checked).
- `figures/figure2/ssp_nbp_annual_2000-2100_4km.png`: annual NBP, one panel per SSP, annual bars and an 11-year
  running mean. Each panel is annotated with the **cumulative** 2024–2100 NBP (+0.49, +2.33, +1.49, +1.45 PgC for
  SSP1-1.9, SSP2-4.5, SSP3-7.0, SSP5-8.5), not a mean (user request 2026-10-01). 2024–2100 mean NBP +0.006 (SSP1-1.9), +0.030 (SSP2-4.5), +0.019 (SSP3-7.0), +0.019 (SSP5-8.5)
  PgC/yr, against +0.051 for 2000–2023 (the later means are small sinks; the 11-year mean dips below zero in
  several decades).

Checks and open points:

- **2023 → 2024 boundary.** The 2024 NBP differs a lot between SSPs (SSP1-1.9 −0.38, SSP5-8.5 −0.63, SSP3-7.0 −0.11,
  SSP2-4.5 +0.12 PgC/yr, against +0.10 in 2023). It is **not** land use or harvest (LAND_USE_FLUX +0.08 to +0.12 and
  WOOD_HARVESTC +0.065 are normal in 2024) but GPP: 2.46 (SSP5-8.5), 2.67 (SSP1-1.9), 2.89 (SSP3-7.0), 3.16
  (SSP2-4.5) against 3.03 in 2023. A forcing-transition artifact would be common to all SSPs, but the sign and size
  differ, which points to each SSP's own weather sequence; not verified. The differences in single years between
  SSPs are therefore mostly weather, not a forced signal; compare SSPs with the running mean or period means.
- **Extreme negative years.** Each SSP has several years far below the historical range (2000–2023 minimum −0.22
  PgC/yr): minimum −0.69 (2086, SSP1-1.9), −0.74 (2054, SSP2-4.5), −0.80 (2056, SSP3-7.0), −1.27 (2094, SSP5-8.5);
  6–10 years per SSP below −0.3. Cause (drought, fire, heat) not yet diagnosed.
- `figures/figure2/ssp_forest_and_cumulative_nbp_2010-2100_4km.png`: the forest-area-change figure and the cumulative-NBP-since-2010
  figure as the two panels (a) and (b) of one new figure (`code/figure2/plot_default_ssp_forest_and_cumnbp.py`, md5
  `b734c456fbb750488bd3d86e21b8936e`, shared legend, same data and colours); the two single-panel figures are kept unchanged.
- `figures/figure2/ssp_nbp_cumulative_2010-2100_4km.png`: cumulative NBP **since 2010** as four coloured lines on one
  panel: the 2010–2023 history in grey (+0.89 PgC by 2023), then each SSP continues from it. At 2050 / 2075 / 2100
  (PgC): SSP1-1.9 +0.47 / +1.61 / +1.38, SSP2-4.5 +1.26 / +1.98 / +3.22, SSP3-7.0 +1.15 / +1.93 / +2.38, SSP5-8.5
  +0.81 / +1.73 / +2.34 (added since 2023: +0.49, +2.33, +1.49, +1.45). All four curves stay positive through the
  century (lowest: +0.21 SSP5-8.5 in 2025, +0.23 SSP3-7.0 in 2056, +0.30 SSP1-1.9 in 2046, +0.54 SSP2-4.5 in 2063; highest:
  +2.26 in 2082, +3.62 in 2095, +2.63 and +3.06 in 2093). The curves wiggle by several tenths of a PgC from single weather
  years. The order SSP2-4.5 > SSP3-7.0 ≈ SSP5-8.5 > SSP1-1.9 holds at 2100 but not along the way: SSP2-4.5 is the
  highest curve in 2027–2038 and from 2085, SSP3-7.0 in 2042–2046 and 2065–2069, SSP5-8.5 in 2078–2081; SSP5-8.5 is the
  lowest in 2024–2030, SSP1-1.9 in 2045–2048, 2068–2075 and 2083–2100. The start year is a parameter (`cumulative_start`);
  versions starting in 2000 or 2024, and the annual-line version, were replaced by this one.
- Forest area at 2024 jumps for SSP1-1.9 (+10.3 ×10³ km² from 2023) and little for the others (+0.2 to +3.5).

### 3.8 Figure 2, presentation versions that show the four SSPs on one slide (2026-10-01)

`code/figure2/plot_management_summary_across_ssps.py`, md5 `8d99f1a1c5cdf8d375e61312d22e9208`, built from the same paired benefit
curves as §3.6 (4 km only):

- `figures/figure2/management_summary_2100_4km.png`: values at 2100, x = the four SSPs; row 1 cumulative NBP benefit
  since 2024, row 2 forest-area change; left RF and RH (36000 s Default), right DF (38000 s Default, own axes).
  RF +3.7 / +4.5 / +5.2 / +5.3 PgC and RH +1.0 / +1.5 / +1.0 / +1.2 PgC (SSP1-1.9 / 2-4.5 / 3-7.0 / 5-8.5), DF +11.2 /
  +11.8 / +10.9 / +10.7; forest area RF +87 / +31 / +174 / +118, RH 0, DF +860 / +916 / +773 / +829 ×10³ km².
- `figures/figure2/management_rf_rh_cumNBP_4ssp_4km.png`: one panel per SSP with the RF and RH cumulative NBP benefit
  curves on a shared axis (DF, ≈ +11 PgC, is on the summary figure).

- `figures/figure2/management_summary_carbon_2100_4km.png`: the carbon-only version of the 2100 summary (one row, RF and RH |
  DF, no forest-area panel), made at the user's request because the forest-area panels of the paired-difference version were
  hard to read (the DF forest panel is just the Default's own forest area, since DF holds zero forest). The original figure is kept.

The ranking DF > RF > RH holds in every SSP; RF varies most between SSPs (3.7 to 5.3 PgC, ≈ 40 %), RH 1.0 to 1.5.
Suggested slide order: one SSP (SSP3-7.0) in full from §3.6 to explain how to read the panels, the summary figure for
the cross-SSP comparison, the other three §3.6 figures as backup.

### 3.9 Figure 2, forest-area change by SSP and management measure (2026-10-01)

`code/figure2/plot_forest_area_by_ssp_management.py`, md5 `fef4fb30418b4c1aa7b7bb6edbcaa874`, from the forest-area extracts of §3.6 (4 km only):
`figures/figure2/forest_area_change_by_ssp_management_4km.png`, one panel per SSP in one row, 2024–2100, each run's own tree-PFT area
minus the 2023 value (804.9 ×10³ km²): RF, RH and the 36000 s Default. DF is **not drawn** (user request: DF is simply "no forest";
the script asserts that every DF forest-area value is 0) and is mentioned in the footnote.

| SSP | Default 2050 | Default 2100 | RF | RH (×10³ km², change since 2023) |
|---|---|---|---|---|
| SSP1-1.9 | +35.7 | +54.8 | +142.3 | +54.8 (= Default) |
| SSP2-4.5 | +52.5 | +111.4 | +142.3 | +111.4 |
| SSP3-7.0 | −19.2 | −31.6 | +142.3 | −31.6 |
| SSP5-8.5 | +9.4 | +24.3 | +142.3 | +24.3 |

RF is identical in every SSP (+5.47 ×10³ km² per year for 26 years, 2024–2049, then fixed at 947.2; 97.0 % of the 1850 forest area
976.0) and RH leaves forest area unchanged (asserted equal to the Default in every year). The documented RF ramp "2024→2050" reaches
its plateau one year earlier in the output (2049).

### 3.10 Figure 4, pool contributions and three boundaries, ELM 4 km SSP3-7.0 (2026-10-01)

First pass of Figure 4 (user decision 2026-10-01: panels a-c only, no strata yet). 4 km, SSP3-7.0,
mean of 2091-2100. RF − Default and RH − Default against the 36000 s Default (blueprint A2).
Extractor `code/figure4/extract_pool_maps.py` (md5 `e36ca89225b8ac1b5b5981652f20661e`): per-gridcell
2091-2100 mean of TOTECOSYSC, TOTVEGC, TOTVEGC_ABG, CWDC, TOTLITC, TOTSOMC (gC/m²) and NBP, NEP,
LAND_USE_FLUX, WOOD_HARVESTC (gC/m²/yr). **Slurm jobs 602350 (Default), 602351 (RF), 602352 (RH)** on
`serial`/`normal`, 1 core, 32 GB, 2 h limit (dedicated partition occupied by another user), all
COMPLETED in 51-58 s, empty stderr. Outputs `_cache/figure4/4km/SSP3-7.0[_RF|_RH]__pools_2091-2100.npz`
on Pathfinder (proj-shared root), copied to the same local path, md5 identical:
`3078046da217df677ccebf2d502ec2c6` (Default), `f33fa43e88e0500d7b1900088af720d7` (RF),
`acf22634b8d215a3a9e2fee1a54e231b` (RH). Plot `code/figure4/plot_pool_strata.py` (md5
`fad48adb4c5dbb91b8934e4eef6876b6`) → `figures/figure4/fig4_pools_4km_SSP3-7.0_2091-2100.{png,csv}`.

Pools: aboveground vegetation = TOTVEGC_ABG; other vegetation = TOTVEGC − TOTVEGC_ABG (roots plus
storage/transfer); CWDC; TOTLITC; TOTSOMC; wood products derived as TOTECOSYSC − (TOTVEGC + CWDC +
TOTLITC + TOTSOMC). All sums area × landfrac weighted over 75,916 valid cells (1,356.1 ×10³ km²).

| pool | Default (PgC) | RF − Default | RH − Default |
|---|---:|---:|---:|
| aboveground vegetation | 8.02 | +4.15 | +0.83 |
| other vegetation | 5.70 | +1.14 | +0.33 |
| coarse woody debris | 2.75 | +0.56 | +0.07 |
| litter | 0.47 | +0.01 | +0.01 |
| soil organic carbon | 26.68 | −0.13 | +0.03 |
| wood products (derived) | 0.88 | −0.76 | −0.31 |
| **total (TOTECOSYSC)** | **44.50** | **+4.97** | **+0.96** |

Three boundaries (RF / RH, PgC): aboveground vegetation +4.15 / +0.83; in-situ ecosystem (excluding
products) +5.73 / +1.27; ecosystem + products +4.97 / +0.96. RF:RH ratio 5.0 / 4.5 / 5.2.

Things to know before interpreting:

- **Cross-check against §3.6:** the TOTECOSYSC differences (RF +4.97, RH +0.96) match that table's
  2100 values for SSP3-7.0 (+5.03, +0.95), which are single-year, here a 10-year mean.
- **Derived products are plausible:** Default 0.88 PgC, positive in every cell (minimum +0.21 gC/m²),
  so TOTPRODC is inside TOTECOSYSC as in blueprint D4. Management lowers the product pool (RF −0.76,
  RH −0.31): the in-situ benefit is larger than the ecosystem + products benefit.
- **SOC: large stock, small and uncertain increment (wording corrected 2026-10-01; the first version
  said "none of the RF benefit").** RF − Default SOC is −0.133 PgC, −0.5 % of the 26.68 PgC SOC stock
  (RH +0.03), against +4.97 PgC in total; aboveground vegetation is 83 % of the RF total (87 % of RH).
  The mean hides a wide spread: 54 % of the land area has a negative ΔSOC, and the area-weighted
  5/25/50/75/95 percentiles of ΔSOC are −749/−197/−7/+67/+249 gC/m², so positive and negative cells
  cancel. The sign is a model result for this scenario and horizon (blueprint E4), not an empirical
  claim, and ELM SOC accuracy is limited (the two observed products agree at r ≈ 0.33, §3.4). A small
  mineral-soil response on decadal scales is what the literature tends to find, and grass-to-forest
  conversion can lower SOC at first (to be checked and cited before use). Test with the strata.
- **Most of the vegetation gain is not land-cover change.** 792 ×10³ km² of land has ΔTOTVEGC > 3000
  gC/m² (mean +5545) and carries 83 % of the total vegetation gain, but the paired forest-area
  difference is only +173.8 ×10³ km² (§3.6). The gain is therefore mostly where RF's region-wide harvest
  ban acts on existing forest, not where it restores forest. This is an inference from the maps
  (ΔTOTVEGC is not a restoration indicator); the strata (`--strata`) decide it.
- RF is restoration **plus** a region-wide harvest ban, and RF − Default also contains the SSP's own
  land-use drift (RF replaces the land trajectory); this is stated in the figure footnote.
- float32 maps: the closure check adds the stocks in float64 (the first run failed a 1e-3 tolerance on
  float32 rounding of ~2e-3 gC/m², not on a real gap).
- Not done: the restoration/protection strata (panels d-f, `--strata`; needs two
  `extract_tree_fraction.py` runs and its thresholds are untested on real data), the other SSPs, the
  0.5° version, an NBP/fire budget panel (COL_FIRE_CLOSS is not in h0).

### 3.11 Figure 4, restoration/protection strata and the increment dose-response, ELM 4 km SSP3-7.0 (2026-10-01)

Extension of §3.10 with panels d-f (`plot_pool_strata.py --strata`). Extractor
`code/figure4/extract_tree_fraction.py` (md5 `382885de4f46211bfc7591900e67cb0e`), per-gridcell tree/shrub/grass/crop
fraction from the h1 `pfts1d_wtgcell` by itype. **Slurm jobs 602366 (transient 2023) and 602367 (RF 2060)**,
`serial`/`normal`, 1 core, 32 GB, both COMPLETED in 3 s, empty stderr. Outputs in
`_cache/figure4/4km/`, copied locally, md5 identical: `transient__treefrac_2023.npz`
`b18772903ccc3a125fa5013748a07819`, `SSP3-7.0_RF__treefrac_2060.npz` `2ae4a87d91c105bc7c49c4e7ed3b8853`.
Checks that passed: tree area 804,878 km² (2023) and 947,158 km² (RF 2060) equal §3.9's 804.9 and 947.2
×10³ km²; the increment is +142.3 ×10³ km²; PFT weights sum to 1.0000 in every land cell; strata sum to the
domain total (RF +4.975, RH +0.955 PgC).

Strata at the default thresholds (increment ≥ 0.01 of the cell; Default WOOD_HARVESTC ≥ 0.1 gC/m²/yr):

| stratum | area (×10³ km²) | RF − Default (PgC, share) | RF (MgC/ha) | RH (MgC/ha) |
|---|---:|---:|---:|---:|
| restoration (+ harvest ban) | 939.0 | +3.88 (78 %) | 41.3 | 6.0 |
| protection only (harvest ban) | 401.2 | +1.04 (21 %) | 25.9 | 9.7 |
| no change | 15.9 | +0.06 (1 %) | 38.4 | 0.0 |

**The threshold strata are not clean and should not be the headline.**

- The restoration increment is thin and widespread, not concentrated: 73.3 % of the land has an
  increment > 0.001, with a mean of 0.143 of the cell. The "restoration" stratum therefore holds 69 % of the
  land and is mostly harvest ban plus a partial conversion.
- The result depends on the threshold: the restoration share of the RF benefit is 79 % (threshold 0.005),
  78 % (0.01), 66 % (0.05) and 53 % (0.10); the area goes 975 → 517 ×10³ km² (12-combination table in
  `fig4_pool_strata_4km_SSP3-7.0_2091-2100_sensitivity.csv`).
- **The "no change" control is not null:** +38 MgC/ha with RH ≈ 0, although neither the increment nor the
  harvest acts there. The likely cause is the drift between RF and Default land use (RF replaces the land
  trajectory, blueprint/scenario caveat 2; Default SSP3-7.0 loses 31.6 ×10³ km² of forest by 2100, §3.9).
  Not verified: the Default land cover (2060) was not extracted.

`code/figure4/check_increment_dose_response.py` (md5 `588a2995a5d7caf8bdcd3666094c06e7`) bins the land by
the size of the increment, a continuous version of the split:

| increment bin | area (×10³ km²) | RF − Default (MgC/ha) | RH − Default | ΔSOC | Default harvest (gC/m²/yr) |
|---|---:|---:|---:|---:|---:|
| ≤ 0.001 (no land-cover change) | 362.6 | 27.9 | 9.9 | +0.75 | 56.8 |
| 0.001-0.01 | 54.6 | 16.1 | 5.2 | +0.38 | 29.1 |
| 0.01-0.05 | 219.8 | 27.6 | 6.5 | +0.58 | 35.3 |
| 0.05-0.1 | 202.6 | 31.5 | 7.2 | +0.06 | 38.7 |
| 0.1-0.2 | 252.7 | 40.7 | 6.8 | −1.48 | 35.6 |
| 0.2-0.5 | 247.5 | 59.1 | 4.2 | −4.96 | 20.9 |
| > 0.5 | 16.4 | 87.1 | 1.1 | −9.73 | 4.9 |

Reading (inference from the bins, not a decomposition; there is no NH run):

- Where RF changes no land cover it still gains +27.9 MgC/ha, about 2.8 × RH: the harvest ban alone is a
  large effect, in the most heavily harvested forest (57 gC/m²/yr). The benefit rises with the increment, to
  +87 MgC/ha where more than half of the cell is converted: the restoration contribution.
- **The SOC response follows the restoration, not the ban:** ΔSOC is ≥ 0 where nothing is converted and falls
  to −9.7 MgC/ha at the largest increments. This is the grass-to-forest SOC decline known from field
  syntheses (Guo & Gifford 2002; Paul et al. 2002, where adding the litter layer reverses the sign), and it
  explains the −0.13 PgC of §3.10.
- A clean split of ban and restoration still needs the NH run; the bins only bound them.

### 3.12 Figure 4, SOC depth and the 2024-2100 trajectories, ELM 4 km SSP3-7.0 (2026-10-01)

**SOC depth in Figure 4 (§3.10-3.11).** `TOTSOMC` is the model's own **full soil-column** SOM carbon, not 0-30 or
0-100 cm. Compared with Figure 1's 0-100 cm integral (`soc_0_100`, 2000-2023 mean, 17.11 PgC, 12.6 kgC/m²), the
4 km SSP3-7.0 Default `TOTSOMC` is 26.17 PgC in 2024 (26.68 in 2091-2100), so about 9 PgC (≈ 35 %) lies below
1 m. The h0 column has 15 layers (`dz_m` in `elm4km_soc_2000-2023.npz`; layer bottoms 0.0175 … 1.38, 2.29, 3.80 m
for layer 10, then bedrock layers to 42 m); how many layers `TOTSOMC` integrates in this ELM version was not
checked (to read in `ColumnDataType.F90`, `nlevdecomp_full`). The ΔSOC of §3.10-3.11 is therefore a whole-column
response; a 0-30 or 0-100 cm ΔSOC would need `TOTSOMC_1m` (in h0) or `SOIL1-4C_vr` added to
`extract_pool_maps.py`. Field studies of afforestation and harvest mostly measure the top 30-100 cm.

**2024-2100 trajectories** (first drawn by a stand-alone script, since 2026-10-01 panels d-e of
`plot_pool_strata.py`, §3.13; input: the annual domain totals of §3.6 in `_cache/figure2/future_4km/`, no new job).
Whole-column SOC (`TOTSOMC`) version, RF − Default, PgC:

| pool | 2030 | 2050 | 2075 | 2100 | mean 2091-2100 | mean 2024-2100 |
|---|---:|---:|---:|---:|---:|---:|
| aboveground vegetation | +0.60 | +2.28 | +3.84 | +4.12 | +4.15 | +2.74 |
| other vegetation | +0.14 | +0.44 | +0.97 | +1.15 | +1.14 | +0.66 |
| CWD | −0.09 | +0.07 | +0.38 | +0.60 | +0.56 | +0.22 |
| SOC | −0.02 | −0.13 | −0.18 | −0.13 | −0.13 | −0.12 |
| products | −0.30 | −0.60 | −0.74 | −0.73 | −0.76 | −0.61 |
| **total** | **+0.31** | **+2.03** | **+4.28** | **+5.03** | **+4.97** | **+2.90** |

RH − Default total: +0.11 (2030), +0.61 (2050), +0.90 (2075), +0.95 (2100); RH SOC is slightly negative until
about 2060 and +0.03 at the end.

- The 2091-2100 mean is the end state of the cumulative response (it equals the 2100 value within 0.06 PgC); it is
  not an average over the horizon. The 2024-2100 time mean (RF +2.90) mixes the ramp-up with the end state and is not
  a benefit: use the end-of-horizon stock difference for the headline and the trajectory for timing.
- Timing: RF reaches 40 % of its 2100 total by 2050 and 85 % by 2075. Products fall at once (−0.60 PgC by 2050) while
  vegetation builds for decades, so the benefit starts small; CWD is negative until about 2045.
- RF's SOC difference declines for about 50 years (minimum −0.18 PgC in 2075) and recovers partly (−0.13 PgC in 2100);
  it is never positive. RH's SOC turns positive late.

### 3.13 Figure 4 with SOC to 1 m and the 2024-2100 trajectory panels, ELM 4 km SSP3-7.0 (2026-10-01)

Redo of the Figure 4 soil carbon at 0-100 cm (`TOTSOMC_1m`) and the trajectories added to the figure (user decision
2026-10-01). Extractor `code/figure4/extract_soc1m.py` (md5 `a5fa0a6a0833882a087dc193b56a8d82`): per case the annual domain
total of `TOTSOMC_1m` for 2024-2100 and the 2091-2100 mean map. **Slurm jobs 602384 (Default), 602385 (RF), 602386 (RH)**,
`serial`/`normal`, 1 core, 32 GB, 4 h limit, COMPLETED in 79-88 s, empty stderr (dedicated partition occupied).
Outputs `_cache/figure4/4km/SSP3-7.0[_RF|_RH]__soc1m_2024-2100.npz`, copied locally, md5 identical:
`29b0d435e0fd77cbd1063458b411c5d0` (Default), `09b6e736d55e816768a310847dcb8ec2` (RF),
`9c35c67530bfe73ab41f8fa667e4c371` (RH). Plot `code/figure4/plot_pool_strata.py` (md5
`2cc55af28cf30fd7f459e6d415fefe63`; `--strata` adds the strata row) → `figures/figure4/fig4_pool_strata_4km_SSP3-7.0_2091-2100.png`
(without `--strata`: `fig4_pools_…png`) and the pool and trajectory CSVs. The superseded stand-alone
`plot_pool_trajectories.py` (md5 `e146edd5068e86e520d20ff178cfc0a7`) was removed.

Seven pools now add up to TOTECOSYSC: aboveground vegetation, other vegetation, CWD, litter, **SOC 0-100 cm
(`TOTSOMC_1m`)**, **SOC below 1 m (`TOTSOMC` − `TOTSOMC_1m`)**, derived wood products. Default 2091-2100 stocks (PgC): 8.02, 5.70, 2.75,
0.47, 17.71, 8.96, 0.88 (total 44.50); the 0-100 cm SOC (17.71 PgC) is 66 % of the whole-column 26.68 PgC.

| pool | RF − Default, 2091-2100 (PgC) | RH − Default |
|---|---:|---:|
| aboveground vegetation | +4.15 | +0.83 |
| other vegetation | +1.14 | +0.33 |
| CWD | +0.56 | +0.07 |
| litter | +0.01 | +0.01 |
| **SOC 0-100 cm** | **−0.156** | **+0.030** |
| SOC below 1 m | +0.023 | −0.002 |
| wood products (derived) | −0.76 | −0.31 |
| total | +4.97 | +0.96 |

- **Checks passed:** the annual totals reproduce the maps exactly (2091-2100 mean of the trajectory vs the map: total
  +4.975 vs +4.975 RF, +0.955 vs +0.955 RH; SOC 0-100 cm −0.156 vs −0.156, +0.030 vs +0.030; below 1 m +0.023 vs +0.023).
  `TOTSOMC_1m` never exceeds `TOTSOMC` in a cell; seven pools sum to TOTECOSYSC.
- **The SOC result holds at 0-100 cm and is a little larger:** RF −0.156 PgC (−0.9 % of the 17.71 PgC top-metre stock),
  not −0.133. The soil below 1 m is nearly unchanged (+0.023), so the loss is in the top metre, where the field
  studies measure. RF's SOC 0-100 cm difference falls for about 50 years (minimum −0.197 PgC in 2075) and recovers
  partly (−0.151 in 2100); it is never positive. RH's is slightly negative until about 2060 (minimum −0.012 in 2039),
  positive from 2064 and +0.036 PgC in 2100.
- The end-state figures of §3.10-3.11 are unchanged except for the SOC split; the strata table of §3.11 is the
  whole-column version of the same maps and its totals did not change.

### 3.14 Figure 3, the management gain at 4 km and at 0.5°, SSP3-7.0 (2026-10-01)

Figure 3 (blueprint E3): the RF gain (RH as a check) of the native 4 km run (C) against the native 0.5° run (A) only; user decision 2026-10-01:
no 4 km-averaged-to-0.5° comparator (an earlier version with C′ was dropped, together with its "variance within 0.5° cells" statistic).
End state = mean of 2091-2100, gain = TOTECOSYSC difference to the 36000 s Default in MgC/ha of land. New 0.5° input: `extract_pool_maps.py`
(md5 `e36ca89225b8ac1b5b5981652f20661e`) on the three native 0.5° runs `20260911_seus_halfdeg_future_ssp370{,_RF,_RH}_dt3600`;
**Slurm jobs 602388 (Default), 602389 (RF), 602390 (RH)**, `serial`/`normal`, 1 core, 8 GB, 1 h limit, COMPLETED in 4-5 s, empty stderr (dedicated
partition occupied). Outputs `_cache/figure3/0.5deg/SSP3-7.0[_RF|_RH]__pools_2091-2100.npz`, copied locally, md5 identical:
`6d386c0aaefaee77cfadd1880d7f00fa` (Default), `c3f34631ed4a3f995fb83eab43a88b5d` (RF), `7fd7279e48d41eb4c31ea898df63d018` (RH). The 4 km input is Figure 4's
`_cache/figure4/4km/` maps (§3.10). Plot `code/figure3/plot_gain_heterogeneity.py` (md5 `82ac6196566cef8c113feda055d598c4`) →
`figures/figure3/fig3_gain_heterogeneity_SSP3-7.0_2091-2100.png`, `fig3_stats_…csv` (all metrics, three subsets, both managements), `fig3_cells_RF_…csv`.

Method: the 4 km grid (324×504) nests exactly in the 0.5° grid (27×42; cell centres equal the means of their 12×12 children, asserted). C and A are compared
on the 4 km grid and on common support (75,920 land cells, 1356.2 ×10³ km², the same at both resolutions), A copied to its 144 children; weights
area × landfrac. A is a separately configured run, so C − A is resolution plus configuration. Panel d is the area-weighted SD of C inside each 0.5° cell
about that cell's own mean (a description of the 4 km variation); the same quantity only chooses the two zoom windows by a rule fixed in code: among 0.5° cells
with ≥ 100 common children, the largest SD and the cell closest to the median SD, 3×3 coarse cells each.

| RF − Default (MgC/ha of land) | mean | SD | q05 | q25 | q50 | q75 | q95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C native 4 km | 36.7 | 27.5 | 2.0 | 16.9 | 30.8 | 50.8 | 91.4 |
| A native 0.5° | 36.5 | 21.4 | 7.1 | 19.1 | 33.1 | 52.2 | 74.1 |

| agreement of A with C, common support | RF | RH |
|---|---:|---:|
| SD(A)/SD(C) | 0.78 | 0.83 |
| weighted Pearson r / Spearman ρ | 0.71 / 0.75 | 0.79 / 0.79 |
| mean absolute / RMS difference (MgC/ha) | 13.6 / 19.6 | 2.3 / 3.3 |
| mean A − C (MgC/ha) | −0.16 | +0.20 |
| top-10 % / bottom-10 % area overlap | 43 % / 52 % | 56 % / 62 % |

- The two runs agree on the regional mean (36.7 vs 36.5 MgC/ha for RF) and differ in the tails: the 0.5° run has a 22 % smaller SD, its 5th and 95th percentiles
  are 7.1 and 74.1 against 2.0 and 91.4 at 4 km.
- Pattern agreement is moderate (RF r 0.71, ρ 0.75). Of the area in the 4 km top decile of the gain, 43 % is also in the 0.5° top decile (RH 56 %); the
  bottom decile 52 % (RH 62 %). The results hold with the 0.5° row 30.5-31.0°N excluded (RF r 0.70, top-decile overlap 43 %) and for cells with ≥ 72 children (r 0.71, 44 %).
- Zoom cells chosen by the rule: zoom 1 is the 0.5° cell at 30.25°N, 92.25°W (southern Louisiana; SD of C 43 MgC/ha, A 58.3), zoom 2 the median-SD cell at 33.75°N,
  85.75°W (SD of C 15.8, A 49.4). No regional reading of the maps was made.
- RF is restoration plus a region-wide harvest ban and its gain contains the SSP's own land-use drift, which differs between the runs only through their own land
  cover. Not done: other SSPs, the downscaled comparator B, the equal-area selection loss of Figure 5.

## 4. Script and product locations

Since 2026-10-01 `code/` and `figures/` are organized by manuscript figure
(`figure1/` … `figure5/`, `supplement/`); `common.py` and `submit_py.sbatch`
stay in `code/`. The Pathfinder scratch mirror still has the older flat
layout.

| Purpose | Location / entry point | Current state |
|---|---|---|
| Main manuscript analysis code and shared case loader | [code/](code/README.md) (per-figure subfolders), shared [code/common.py](code/common.py) | Legacy figure scripts; case mapping must be updated before selected-cohort reruns |
| Pathfinder batch wrapper | [code/submit_py.sbatch](code/submit_py.sbatch) | Runs a specified Python script from the manuscript analysis root; resources and remote paths must be checked before use |
| Historical AGB/SOC extraction | [poster extraction script](../carbon_offset_poster/codes/extract_biomass_soc.py) and its [batch wrapper](../carbon_offset_poster/codes/submit_py.sbatch) | Separate poster workflow; output directory is a command argument |
| Observational comparison plot | [poster panel script](../carbon_offset_poster/codes/plot_biomass_soc_panel.py) | Local plotting from extracted ELM cache and local observation files |
| Generated manuscript plots | Pathfinder: `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/figures/figureN/<PAPER_COHORT>/` (`figure_outdir()` in `code/common.py`); local Figure 1 plots in `figures/figure1/` | Local `figures/legacy/` PNGs are old-cohort figures and not current evidence |
| Intermediate numerical cache | `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/_cache/<PAPER_COHORT>/` (legacy scripts); `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/_cache/obs_compare/` (Figure 1 extracts) | Script cache keys lack a complete source-version signature; never reuse across case-map changes without explicit validation |
| Slurm logs | `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/logs/` | Generated job output; do not commit |

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
