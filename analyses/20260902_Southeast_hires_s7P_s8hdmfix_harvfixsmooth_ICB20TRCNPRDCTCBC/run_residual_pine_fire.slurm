#!/bin/bash
#SBATCH --account=hpcl-cli185
#SBATCH --partition=serial
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --job-name=pine405fire
#SBATCH --output=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/pine405fire-%j.out
#SBATCH --error=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/pine405fire-%j.err
set -euo pipefail
unset SLURM_EXPORT_ENV
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
ANALYSIS_ROOT=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC
ANALYSIS_PYTHON=/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python
cd "$ANALYSIS_ROOT"
# Separate output directory for each execution; preserve all earlier results.
srun "$ANALYSIS_PYTHON" "$ANALYSIS_ROOT/diagnose_residual_pine_fire.py" \
  --output-dir "$ANALYSIS_ROOT/outputs/residual_pine_fire_${SLURM_JOB_ID}"
