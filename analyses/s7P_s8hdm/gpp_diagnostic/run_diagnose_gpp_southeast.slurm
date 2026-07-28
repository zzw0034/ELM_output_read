#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -t 0:10:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2
#SBATCH --mem=8gb
#SBATCH -J diagGPP
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/gpp_diagnostic/diagGPP-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/gpp_diagnostic/diagGPP-%j.err

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/gpp_diagnostic"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"
export NC_PATH="/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260712_Southeast_hires_s7P_s8hdm_ICB1850CNPRDCTCBC/run/20260712_Southeast_hires_s7P_s8hdm_ICB1850CNPRDCTCBC.elm.h0.0361-01-01-00000.nc"
export SURFDATA_PATH="/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260712_Southeast_hires_s7P_s8hdm_ICB1850CNPRDCTCBC/run/surfdata.nc"
export OUT_DIR="${WORKDIR}/results_v2"

unset SLURM_EXPORT_ENV
mkdir -p "${OUT_DIR}"
cd "${WORKDIR}"
"${PYTHON}" "${WORKDIR}/diagnose_gpp_southeast.py"
