#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2
#SBATCH --mem=32gb
#SBATCH -J plotHDMfire
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/plotHDMfire-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm/plotHDMfire-%j.err

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/s7P_s8hdm"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"
NC_PATH="/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC/run/20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC.elm.h0.0321-01-01-00000.nc"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" "${WORKDIR}/plot_hdm_fire_maps.py" "${NC_PATH}"
