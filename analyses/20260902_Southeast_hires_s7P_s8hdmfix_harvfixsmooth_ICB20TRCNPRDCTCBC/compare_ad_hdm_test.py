"""
Verdict script for the AD spin-up HDM experiment.

The question this run exists to answer: the pine PFT went to zero leaf carbon on
9% of pine patches during the original AD spin-up, which ran with human
population density stuck at zero because the CPL_BYPASS HDM reader had its
dimensions hardcoded to 720x360 against a 504x324 file and never checked the
NetCDF return code. Fire is strongly implicated but was never proven. This
compares a rerun of the same AD spin-up, same everything, with an E3SM source
that reads HDM correctly.

    control     20260712_..._s7P_s8hdm_ICB1850CNRDCTCBC_ad_spinup     HDM = 0
    experiment  20260909_..._s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup

Reports, at each 20-year checkpoint the spin-up writes:

  1. HDM. If it is still zero the experiment is void; stop and find out why.
  2. COL_FIRE_CLOSS, to confirm suppression actually changed the fire regime.
  3. The pine dead fraction, against the control's 1.0 / 6.6 / 7.8 / 8.9%.
  4. NDEP_TO_SMINN. The source tree also gained a Ndep calendar-year fix
     between the two runs; if this matches the control the change was a no-op
     here and the experiment cleanly isolates HDM.

Runs on Pathfinder (the h1 files are on scratch and proj-shared, and the conda
env there has netCDF4). Usage: python compare_ad_hdm_test.py
"""

import glob
import os
import re

import numpy as np
import netCDF4 as nc

CONTROL = ("/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/"
           "20260712_Southeast_hires_s7P_s8hdm_ICB1850CNRDCTCBC_ad_spinup/run")
EXPERIMENT = ("/scratch/hpcl-cli185/zw5/cime_output_dirs/"
              "20260909_Southeast_hires_s7P_s8hdmfixTEST_ICB1850CNRDCTCBC_ad_spinup/run")
NLAT, NLON = 324, 504
DEAD = 0.5              # annual mean TLAI below this counts as a dead patch
PINE = 1                # needleleaf evergreen temperate tree
NATVEG = 1              # natural vegetation landunit
MIN_WEIGHT = 0.05       # ignore slivers


def _annual_mean(var):
    """These files hold one 20-year-mean record, but average defensively."""
    return np.nanmean(
        np.stack([np.ma.filled(var[t, :], np.nan).astype(np.float32)
                  for t in range(var.shape[0])]), axis=0)


def pine_lai(h1_path):
    """Pine annual-mean LAI on the lat/lon grid, NaN where there is no pine."""
    d = nc.Dataset(h1_path)
    ix = d.variables["pfts1d_ixy"][:].astype(np.int32) - 1
    jy = d.variables["pfts1d_jxy"][:].astype(np.int32) - 1
    it = d.variables["pfts1d_itype_veg"][:].astype(np.int16)
    lu = d.variables["pfts1d_itype_lunit"][:].astype(np.int16)
    wt = np.ma.filled(d.variables["pfts1d_wtgcell"][:].astype(np.float32), 0.0)
    lai = _annual_mean(d.variables["TLAI"])
    d.close()
    sel = (it == PINE) & (lu == NATVEG) & (wt > MIN_WEIGHT) & np.isfinite(lai)
    out = np.full((NLAT, NLON), np.nan, np.float32)
    out[jy[sel], ix[sel]] = lai[sel]
    return out


def gridcell_fields(h0_path, names):
    d = nc.Dataset(h0_path)
    out = {}
    for n in names:
        if n in d.variables:
            a = np.ma.filled(d.variables[n][:].astype(float), np.nan)
            out[n] = np.nanmean(a, axis=0) if a.ndim == 3 else a
    d.close()
    return out


def column_fire(h1_path):
    """COL_FIRE_CLOSS is column-level; weight it up to the gridcell."""
    d = nc.Dataset(h1_path)
    if "COL_FIRE_CLOSS" not in d.variables:
        d.close()
        return None
    cx = d.variables["cols1d_ixy"][:].astype(np.int32) - 1
    cj = d.variables["cols1d_jxy"][:].astype(np.int32) - 1
    cw = np.ma.filled(d.variables["cols1d_wtgcell"][:].astype(np.float32), 0.0)
    cm = _annual_mean(d.variables["COL_FIRE_CLOSS"])
    d.close()
    num = np.zeros((NLAT, NLON))
    den = np.zeros((NLAT, NLON))
    ok = np.isfinite(cm) & (cw > 0)
    np.add.at(num, (cj[ok], cx[ok]), cm[ok] * cw[ok])
    np.add.at(den, (cj[ok], cx[ok]), cw[ok])
    with np.errstate(invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)


def years_available(run_dir):
    ys = []
    for p in glob.glob(os.path.join(run_dir, "*.elm.h1.*.nc")):
        m = re.search(r"\.h1\.(\d{4})-", os.path.basename(p))
        if m:
            ys.append(int(m.group(1)))
    return sorted(ys)


def path_for(run_dir, tape, year):
    hits = glob.glob(os.path.join(run_dir, f"*.elm.{tape}.{year:04d}-01-01-00000.nc"))
    return hits[0] if hits else None


def main():
    ctrl_years = years_available(CONTROL)
    expt_years = years_available(EXPERIMENT)
    shared = [y for y in expt_years if y in ctrl_years and y != 1]
    print(f"control checkpoints   {ctrl_years}")
    print(f"experiment checkpoints {expt_years}")
    if not shared:
        print("\nNo comparable checkpoint yet. The first one lands at year 21.")
        return
    print(f"\ncomparing at {shared}\n")

    print(f"{'year':>5s} | {'HDM mean':>18s} | {'fire loss':>19s} | "
          f"{'pine dead %':>17s} | {'Ndep':>17s}")
    print(f"{'':>5s} | {'ctrl':>8s} {'expt':>9s} | {'ctrl':>9s} {'expt':>9s} | "
          f"{'ctrl':>8s} {'expt':>8s} | {'ctrl':>8s} {'expt':>8s}")
    for y in shared:
        row = {}
        for tag, run in (("ctrl", CONTROL), ("expt", EXPERIMENT)):
            h0, h1 = path_for(run, "h0", y), path_for(run, "h1", y)
            g = gridcell_fields(h0, ["HDM", "NDEP_TO_SMINN"]) if h0 else {}
            row[f"{tag}_hdm"] = np.nanmean(g["HDM"]) if "HDM" in g else np.nan
            row[f"{tag}_ndep"] = (np.nanmean(g["NDEP_TO_SMINN"])
                                  if "NDEP_TO_SMINN" in g else np.nan)
            f = column_fire(h1) if h1 else None
            row[f"{tag}_fire"] = np.nanmean(f) if f is not None else np.nan
            lai = pine_lai(h1) if h1 else None
            ok = np.isfinite(lai) if lai is not None else None
            row[f"{tag}_dead"] = (100 * np.mean(lai[ok] < DEAD)
                                  if ok is not None and ok.sum() else np.nan)
        print(f"{y:5d} | {row['ctrl_hdm']:8.3f} {row['expt_hdm']:9.3f} | "
              f"{row['ctrl_fire']:9.3g} {row['expt_fire']:9.3g} | "
              f"{row['ctrl_dead']:7.1f}% {row['expt_dead']:7.1f}% | "
              f"{row['ctrl_ndep']:8.3g} {row['expt_ndep']:8.3g}")

    last = shared[-1]
    lc, le = pine_lai(path_for(CONTROL, "h1", last)), pine_lai(path_for(EXPERIMENT, "h1", last))
    ok = np.isfinite(lc) & np.isfinite(le)
    dc, de = ok & (lc < DEAD), ok & (le < DEAD)
    print(f"\nat year {last}: control kills {int(dc.sum())} pine patches, "
          f"experiment kills {int(de.sum())}")
    print(f"  of the control's dead patches, still dead in the experiment: "
          f"{int((dc & de).sum())} ({100*(dc & de).sum()/max(dc.sum(),1):.1f}%)")
    print(f"  their mean LAI in the experiment: {np.nanmean(le[dc]):.3f}"
          f"   (surviving pine there: {np.nanmean(le[ok & ~de]):.3f})")
    print("\nVerdict: a rescued fraction near 100% means the missing fire "
          "suppression caused the dieback;\nnear 0% means HDM was not the cause "
          "and the temperature pathway needs revisiting.")


if __name__ == "__main__":
    main()
