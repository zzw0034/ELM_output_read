#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=16gb
#SBATCH -t 01:00:00
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000/logs/%x-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000/logs/%x-%j.err

# Generic runner: sbatch -J <name> submit_py.sbatch <script.py> [args...]
# Same pattern as ../20260911_seus_halfdeg_dt3600/submit_py.sbatch: all
# Python analysis goes through Slurm, never the login node.
# The logs/ directory must exist before submission (Slurm opens -o/-e first).

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" -u "$@"
