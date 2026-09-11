#!/bin/bash
#SBATCH --account=hpcl-cli185
#SBATCH --partition=serial
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --job-name=zerogpp
#SBATCH --output=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/zerogpp-%j.out
#SBATCH --error=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/zerogpp-%j.err
set -euo pipefail
unset SLURM_EXPORT_ENV
A=/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC
PY=/projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf/bin/python
RUN=/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup/run
C=20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup
cd "$A"
srun "$PY" "$A/locate_zero_gpp_cells.py" \
  --h0 "$RUN/$C.elm.h0.0001-01-01-00000.nc" \
  --h1 "$RUN/$C.elm.h1.0001-01-01-00000.nc" \
  --out "$A/outputs/zero_gpp_${SLURM_JOB_ID}/report.json"
