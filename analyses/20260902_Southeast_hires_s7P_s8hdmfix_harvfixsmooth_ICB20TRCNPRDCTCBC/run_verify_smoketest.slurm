#!/bin/bash
#SBATCH --account=hpcl-cli185
#SBATCH --partition=serial
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --job-name=prodverify
#SBATCH --output=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/prodverify-%j.out
#SBATCH --error=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/prodverify-%j.err
set -euo pipefail
unset SLURM_EXPORT_ENV
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
A=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC
PY=/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python
cd "$A"
srun "$PY" "$A/verify_smoketest.py" \
  --run-dir /scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup/run \
  --out "$A/outputs/production_verify_${SLURM_JOB_ID}/report.json"
