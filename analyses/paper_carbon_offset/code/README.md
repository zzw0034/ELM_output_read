# Analysis code

Organized by manuscript figure since 2026-10-01: each `figureN/` holds the
scripts for main Figure N (see [the manuscript plan](../MANUSCRIPT_BLUEPRINT.md),
Part E figures, Part D methods), `supplement/` holds supporting diagnostics,
and the shared pieces stay here:

- `common.py`: the single case map and common loader. Scripts in the
  subfolders add `code/` to `sys.path` to import it, and write to
  `figure_outdir("<folder>")` = `../figures/<folder>/<PAPER_COHORT>/` on
  Pathfinder. Caches stay in `../_cache/<PAPER_COHORT>/`.
- `submit_py.sbatch`: the Slurm runner (run from the analysis root).

The `fig0N_*` filenames are stable legacy asset IDs, not the new figure
numbers; they are exploratory scripts awaiting rework. Read the
[case matrix](../CASE_MATRIX.md) before interpreting their output. Legacy PNGs
are preserved in `../figures/legacy/`.

## figure1/ — observational evaluation (Results 3.1)

| Script | What it does | How it runs |
|---|---|---|
| `obs_fetch_esacci_agb_v7_seus.py` | ESA CCI Biomass v7.0 1 km AGB/AGB_SD, all 18 epochs, SEUS box 24–37.5°N, 95–74°W → `/projects/hpcl-cli185/proj-shared/zw5/obs_data/biomass/` | 2026-09-24 on the Pathfinder login node (network transfer only, HTTP byte-range read from CEDA), streamed over ssh stdin with the `make_surfdata_pf` python; values unchanged (oven-dry biomass, Mg/ha, ocean = 0) |
| `extract_elm_4km_tree_stemc.py` | ESA-matched ELM quantity at either resolution: tree-PFT (itype 1–8) LIVESTEMC+DEADSTEMC × wtgcell per gridcell, plus per-type density and fraction; day-weighted annual means for the ESA epochs 2005–2012, 2015–2023 | Slurm via `submit_py.sbatch`; outputs to `_cache/obs_compare/` under the remote root `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset` |
| `plot_obs_esacci_agb_v7_mean.py` | Multi-epoch mean map of the ESA AGB file | Locally (cartopy venv), from `_cache/obs/` |
| `plot_elm_vs_esacci_agb.py` | ELM 4 km tree stem C alone and side by side with ESA × carbon fraction | Locally |
| `plot_agb_elm4km_esa4km_elm0p5.py` | ELM 4 km \| ESA aggregated to 4 km \| ELM 0.5° copied to 4 km; everything and all statistics on the 4 km grid, common support | Locally |
| `plot_agb_4km_comparators.py` | All on the 4 km grid: ELM 4 km (C), ESA, 0.5° copied (A), 0.5° downscaled by 4 km tree-PFT fractions (B); common-support and within-0.5° anomaly statistics | Locally |
| `obs_soc_soilgrids_wcs_4km.py` | SoilGrids 2.0 SOC 0–30 / 0–100 cm on the ELM 4 km grid: `fetch` (ISRIC WCS, login node, network only) and `process` (Slurm) → `/projects/hpcl-cli185/proj-shared/zw5/obs_data/SOC/soilgrids/` | 2026-10-01, jobs 602046; see notes §3.4 |
| `obs_soc_hwsd_v12_4km.py` | HWSD v1.2 (0.05°) SOC 0–30 / 0–100 cm remapped to the 4 km grid with overlap weights → `.../obs_data/SOC/hwsd/` | Slurm, job 602047 |
| `extract_elm_soc.py` | ELM SOC 0–30 cm (SOIL1–4C_vr) and 0–100 cm (TOTSOMC_1m), annual day-weighted means 2000–2023, both resolutions → `_cache/obs_compare/` | Slurm via `submit_py.sbatch`, jobs 602050/602051 |
| `plot_soc_elm4km_obs4km_elm0p5.py` | ELM 4 km \| obs on 4 km \| ELM 0.5° copied to 4 km (everything and all statistics on the 4 km grid), rows 0–30 and 0–100 cm, one figure per product | Locally |

Local plotting scripts read inputs pulled into `../_cache/` and write PNGs to
`../figures/figure1/` (git-ignored).

## Legacy and diagnostic scripts

| Folder | Script | Intended use | Required work |
|---|---|---|---|
| `figure2/` | `fig01_offset_potential_timeseries.py` | Main Figure 2 | Recompute regional RF/RH/DF benefits across SSPs |
| `figure3/` | `fig02_offset_potential_maps.py` | Main Figure 3 (or supplement) | Harmonize mask and area-weighted spatial summaries |
| `figure3/` | `fig04_resolution_comparison.py` | Main Figure 3 heterogeneity; its regional-total panels also feed Figure 2 | Extend aggregation comparison from DF to RF |
| `figure4/` | `fig03_carbon_pool_partitioning.py` | Main Figure 4 | Close pool sums against native TOTECOSYSC |
| `figure4/` | `check_nbp_decline_decomposition.py` | Mechanism/accounting support | Validate the NBP components for the selected cohort |
| `figure5/` | `fig05_siting_potential_vs_vulnerability.py` | Starting point for Main Figure 5 | Replace quadrants with equal-area selection; audit risk definitions |
| `supplement/` | `fig06_fire_impact.py` | Supplement / vulnerability support | Use complete fire budget and account for HDM effective resolution |
| `supplement/` | `check_df_grass_decomposition.py`, `check_grass_phenology_mechanism.py` | Supplementary diagnostics | Interpret alongside corrected daylength runs |

Still missing: the quantitative SOC evaluation (the maps and first-look statistics exist, see notes §3.4),
the observational ceiling, and the equal-area selection experiment.

## Running on Pathfinder

From the **analysis root** (the parent of this directory), the approved-run
command shape is:

```bash
sbatch --export=NONE -J <name> code/submit_py.sbatch code/<folder>/<script.py> [args...]
```

The Pathfinder root of this paper folder is
`/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset/` (persistent,
same layout as here); `submit_py.sbatch` and `common.py` point there. Sync
`local -> remote` before running. The older scratch copy under
`ELM_output_read/analyses/` is superseded. This is not authorization for remote
synchronization or submission. Follow the project AGENTS.md, verify remote
files and resources, and submit only after the required approval.
