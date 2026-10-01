# CLAUDE.md — paper_carbon_offset

Loaded automatically when working in this folder. It only points to the
governing documents; if anything here disagrees with them, they win. The
workspace `AGENTS.md` rules (SSH, Slurm, sync, destructive actions) still
apply in full.

## Where this folder lives on Pathfinder

- **Remote root:** `/projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset`
  (declared on the first line of [README.md](README.md); persistent
  proj-shared, same layout as this folder). This differs from the scratch
  root of the rest of `ELM_output_read`.
- `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/` is
  the **original backup** (its own README says so). Do not run, edit or
  sync into it.
- Before writing anything to `/scratch`, check
  `lfs quota -p 55528 -h /scratch`: the project quota was over its limit
  with the grace period expired (2026-09-29 to 2026-10-01), which makes
  writes fail, sometimes disguised as "NetCDF: HDF error".

## Read before working on the paper

1. [README.md](README.md): status, boundaries, directory map.
2. [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md), **Part A** (the only
   statement of current decisions), then the Methods (Part D) and figure
   (Part E) section for the task.
3. [analysis_process_notes.md](analysis_process_notes.md): data locations,
   sources, processing conventions, extracts with md5 and job IDs.

## Layout and workflow

- `code/figureN/`, `figures/figureN/` (N = 1–5) and `supplement/` subfolders;
  `code/common.py` and `code/submit_py.sbatch` are shared. See
  [code/README.md](code/README.md).
- Edit here → commit → sync the needed files `local -> remote` to the remote
  root (no `--delete`) → submit from the remote root with
  `sbatch --export=NONE ... code/submit_py.sbatch code/<folder>/<script.py>`.
  Summarize host, paths, resources and command and get approval first.
- `_cache/` and figures are git-ignored; durable extracts live under the
  remote root (`_cache/obs_compare/` etc.), observations under
  `/projects/hpcl-cli185/proj-shared/zw5/obs_data/`.
- Record new extracts (path, md5, job ID, script version) in
  `analysis_process_notes.md`, and decisions in blueprint Part A, in the
  same commit as the work.
