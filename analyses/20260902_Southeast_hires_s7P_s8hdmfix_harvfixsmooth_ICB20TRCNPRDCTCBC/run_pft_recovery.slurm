#!/bin/bash
#SBATCH --account=hpcl-cli185
#SBATCH --partition=serial
#SBATCH --qos=normal
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=1
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --job-name=pftrecov
#SBATCH --output=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/pftrecov-%j.out
#SBATCH --error=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/pftrecov-%j.err
set -euo pipefail
unset SLURM_EXPORT_ENV
A=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC
PY=/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python
cd "$A"
srun "$PY" "$A/compare_pft_recovery.py" \
  --run-dir /scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup/run \
  --case 20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup \
  --cells "$A/outputs/residual_pine_fire_522677/residual_trajectory.csv" \
  --out "$A/outputs/pft_recovery_${SLURM_JOB_ID}/report.json"
