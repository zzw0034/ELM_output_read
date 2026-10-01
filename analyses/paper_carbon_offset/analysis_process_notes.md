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
