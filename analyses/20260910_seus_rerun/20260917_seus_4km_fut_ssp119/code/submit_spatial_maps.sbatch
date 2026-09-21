#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p hpcl-cli185
#SBATCH -q hpcl-cli185
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=120gb
#SBATCH -t 02:00:00
#SBATCH -J ssp119_4km_spatial
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260917_seus_4km_fut_ssp119/code/logs/spatial-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260917_seus_4km_fut_ssp119/code/logs/spatial-%j.err

# On the project's own dedicated partition, not the shared 'serial' pool --
# see ../../../20260908_seus_4km/ANALYSIS_NOTES.md for why that pool was
# unpredictably slow/contended for this 4km case family (2026-09-14).

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260917_seus_4km_fut_ssp119/code"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

mkdir -p "${WORKDIR}/logs"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" -u "${WORKDIR}/plot_spatial_maps.py"
