#!/bin/bash -e
#SBATCH -p serial
#SBATCH -q normal
#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2
#SBATCH --mem=32gb
#SBATCH -J plotADspinEv
#SBATCH -o plotADspinEv-%J.out
#SBATCH -e plotADspinEv-%J.err

# Layout on Pathfinder (project hpcl-cli185):
#   /scratch/hpcl-cli185/zw5/ELM_output_read/                      (REPO_ROOT, copy of this repo)
#       elmtools/                                                  (helper package, needed by the script)
#       analyses/4cases_FmaxF0soilcolor/
#           run_plot_carbon_maps_adspin_smooth_Everything.slurm     (this file)
#           plot_carbon_maps_adspin.py                             (plotting script)
#           outputs/<run_name>/{GPP,NEE,TOTVEGC,TOTSOMC}.{png,tif}  (output -> here)
#
# NOTE: plot_carbon_maps_adspin.py finds elmtools via a relative
#   sys.path.insert(__file__/../..) -- so the whole repo tree (at least
#   elmtools/ + analyses/4cases_FmaxF0soilcolor/) must be copied over,
#   not just this .py file in isolation.
#
# Usage:
#   sbatch run_plot_carbon_maps_adspin_smooth_Everything.slurm
WORKDIR="/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/4cases_FmaxF0soilcolor"

cd "${WORKDIR}"

RUN_DIR="/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260624_Southeast_hires_s8_smoothEverthing_ICB1850CNRDCTCBC_ad_spinup/run"
RUN_NAME="20260624_Southeast_hires_s8_smoothEverthing_ICB1850CNRDCTCBC_ad_spinup"

# Two ad-spinup snapshots to plot for this case.
NC_PATHS=(
    "${RUN_DIR}/${RUN_NAME}.elm.h0.0021-01-01-00000.nc"
    "${RUN_DIR}/${RUN_NAME}.elm.h0.0061-01-01-00000.nc"
)

# Reuse the env created for s6 (make_surfdata_pf); it already has
# xarray / scipy / netcdf4 / matplotlib-base / cartopy / rasterio.
source /software/baseline/nsp/miniforge3/24.11.3-0/etc/profile.d/conda.sh
conda activate /projects/hpcl-cli185/proj-shared/zw5/conda_envs/make_surfdata_pf

# Matplotlib has no display on a compute node -- force the Agg backend so
# the PNGs still write cleanly and no GUI hooks are touched.
export MPLBACKEND=Agg

for NC_PATH in "${NC_PATHS[@]}"; do
    python "${WORKDIR}/plot_carbon_maps_adspin.py" "${NC_PATH}"
done
