#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p hpcl-cli185
#SBATCH -q hpcl-cli185
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=120gb
#SBATCH -t 02:00:00
#SBATCH -J mgmt6_gpp_spatial
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260915_seus_4km_fut_management_scenarios/code/logs/spatial-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260915_seus_4km_fut_management_scenarios/code/logs/spatial-%j.err

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260915_seus_4km_fut_management_scenarios/code"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

mkdir -p "${WORKDIR}/logs"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" -u "${WORKDIR}/plot_gpp_spatial_maps.py"
