#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4
#SBATCH --mem=32gb
#SBATCH -J extractAnnualTS
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260901_seus_halfdeg_transient/extractAnnualTS-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260901_seus_halfdeg_transient/extractAnnualTS-%j.err

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260901_seus_halfdeg_transient"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" "${WORKDIR}/extract_annual_timeseries.py"
