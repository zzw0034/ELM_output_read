#!/bin/bash -e
#SBATCH -A hpcl-cli185
#SBATCH -p hpcl-cli185
#SBATCH -q hpcl-cli185
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=32gb
#SBATCH -t 01:00:00
#SBATCH -o /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/carbon_offset_poster/logs/%x-%j.out
#SBATCH -e /scratch/hpcl-cli185/zw5/ELM_output_read/analyses/carbon_offset_poster/logs/%x-%j.err

# Generic runner: sbatch -J <name> [-w <idle node>] [--mem=<override>] submit_py.sbatch <script.py> [args...]
#
# All Python analysis in this project runs through Slurm, no exceptions
# (see ../../paper_carbon_offset/AI_HANDOFF.md and AGENTS.md -- no
# login-node exception for "small" jobs). Use the project's dedicated
# hpcl-cli185 partition, not the shared 'serial' pool.
#
# --mem default (32gb) suits the 0.5 deg (27x42) extraction; override with
# `sbatch --mem=128gb ...` for the 4 km (324x504) extraction, which loads
# 4 depth-resolved SOC pools per year.

set -u

WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/carbon_offset_poster/codes"
PYTHON="/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python"

unset SLURM_EXPORT_ENV
export MPLBACKEND=Agg

mkdir -p "${WORKDIR}/../logs"
cd "${WORKDIR}"
"${PYTHON}" -u "$@"
