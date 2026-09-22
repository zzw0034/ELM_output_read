#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p hpcl-cli185
#SBATCH -q hpcl-cli185
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=64g
#SBATCH -t 04:00:00
#SBATCH --array=0-7%4
#SBATCH -J compare4km_extract
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/rerun_comparison/logs/%x-%A_%a.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/rerun_comparison/logs/%x-%A_%a.err

set -u
unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/rerun_comparison"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"
KEYS=(transient ssp119 ssp245 ssp370 ssp370_RF ssp370_DF ssp370_RH ssp585)

cd "${WORKDIR}"
"${PYTHON}" -u extract_pair.py "${KEYS[${SLURM_ARRAY_TASK_ID}]}"
