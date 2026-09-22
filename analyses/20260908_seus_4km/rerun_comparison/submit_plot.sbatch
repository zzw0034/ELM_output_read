#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p hpcl-cli185
#SBATCH -q hpcl-cli185
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=32g
#SBATCH -t 01:00:00
#SBATCH -J compare4km_plot
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/rerun_comparison/logs/%x-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/rerun_comparison/logs/%x-%j.err

set -u
unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260908_seus_4km/rerun_comparison"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

cd "${WORKDIR}"
"${PYTHON}" -u plot_comparison.py
