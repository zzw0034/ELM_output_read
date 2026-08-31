#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=128G
#SBATCH -J finidatQC441
#SBATCH -o /projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC/run/finidatQC441-%j.out
#SBATCH -e /projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC/run/finidatQC441-%j.err

set -u

WORKDIR="/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260717_Southeast_hires_s7P_s8hdmfix_ICB1850CNPRDCTCBC/run"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

unset SLURM_EXPORT_ENV

cd "${WORKDIR}"
"${PYTHON}" "${WORKDIR}/check_finidat_qc.py"
