#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2
#SBATCH --mem=32gb
#SBATCH -J plotUrbanPFT
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/plotUrbanPFT-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/plotUrbanPFT-%j.err

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"
SURFDATA_PATH="/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260712_Southeast_hires_s7P_s8hdm_ICB1850CNPRDCTCBC/run/surfdata.nc"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" "${WORKDIR}/plot_urban_pft_maps.py" "${SURFDATA_PATH}"
