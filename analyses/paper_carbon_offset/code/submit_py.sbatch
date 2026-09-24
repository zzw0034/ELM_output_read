#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p hpcl-cli185
#SBATCH -q hpcl-cli185
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=32gb
#SBATCH -t 03:00:00
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/logs/%x-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/logs/%x-%j.err

# Generic runner from the analysis root:
# sbatch --export=NONE -J <name> code/submit_py.sbatch code/<script.py> [args...]
# Existing resources and paths are retained, not newly validated. Follow
# AI_HANDOFF.md / AGENTS.md: verify source cohort, paths, environment and logs;
# obtain the required staging/submission approval and use sbatch --test-only.
# Figure filename numbers are legacy IDs; see manuscript_figure_results_discussion.md.
#
# Use the project's own hpcl-cli185 partition, not the shared 'serial' pool:
# see ../20260908_seus_4km/ANALYSIS_NOTES.md for the session where serial-pool
# jobs were unpredictably slow (18 min to repeated 2-hour timeouts) because of
# other users' CPU load on the same nodes, while dedicated-partition idle
# nodes ran the identical work in ~12 minutes.

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

cd "${WORKDIR}"
"${PYTHON}" -u "$@"
