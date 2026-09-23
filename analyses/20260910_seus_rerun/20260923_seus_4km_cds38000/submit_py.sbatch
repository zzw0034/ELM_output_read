#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=32gb
#SBATCH -t 04:00:00
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260923_seus_4km_cds38000/logs/%x-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260923_seus_4km_cds38000/logs/%x-%j.err

# Generic runner: sbatch -J <name> submit_py.sbatch <script.py> [args...]
# e.g.  sbatch -J cds4km_585 submit_py.sbatch analyze_4km_cds38000.py ssp585
# Same pattern as ../20260922_seus_halfdeg_DF_cds38000/submit_py.sbatch; memory
# and walltime are larger because each 4 km h1 file is ~7.5 GB (2.44 M PFTs):
# per SSP the script reads 4 runs x 20 h1 years plus 4 x 77 h0 years.
# The logs/ directory must exist before submission (Slurm opens -o/-e first).

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260910_seus_rerun/20260923_seus_4km_cds38000"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" -u "$@"
