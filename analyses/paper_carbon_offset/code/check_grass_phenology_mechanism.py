"""
Historical screening of monthly domain-mean Default BTRAN/TLAI by PFT.

This script does not read phenology trigger parameters or compare paired
forest-to-grass conversion sites. Domain means cannot establish whether local
water, temperature or daylength thresholds are crossed. Retained green leaf
area motivates further checking; it does not prove inflated GPP.

Newer evidence in ../CRIT_DAYL_STRESS_ARTIFACT.md identifies a 36000 s
daylength threshold and spatial discontinuity near 30.833 N, and documents
paired 0.5-degree Default/DF sensitivity at 38000 s. Use that record and
DF_GRASS_SENSITIVITY.md for current status, not this screening alone.

Usage inside an approved Slurm allocation:
    python code/check_grass_phenology_mechanism.py [year] [0.5deg|4km]
"""
import sys

import numpy as np
import xarray as xr

from common import HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, h1_files

PFT_NAMES = {1: "NET_temp", 7: "BDT_temp", 9: "BES_temp", 10: "BDS_temp",
             13: "C3_grass", 14: "C4_grass", 15: "crop_unmanaged"}
PHENOLOGY = {1: "evergreen", 7: "season_decid", 9: "evergreen",
             10: "stress_decid", 13: "stress_decid", 14: "stress_decid",
             15: "stress_decid"}


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2100
    res = sys.argv[2] if len(sys.argv) > 2 else "0.5deg"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)
    case = cases["SSP3-7.0"]

    files = [f for f in h1_files(case, subdir) if f"h1.{year:04d}-" in f]
    if not files:
        print(f"no h1 file for {year} in {case}")
        sys.exit(1)

    ds = xr.open_dataset(files[0], decode_times=False)
    itype = ds["pfts1d_itype_veg"].values.astype(int)
    wt_frac = np.where(np.isfinite(ds["pfts1d_wtgcell"].values), ds["pfts1d_wtgcell"].values, 0.0)
    # Weight by physical gridcell area, not the dimensionless wtgcell fraction
    # alone -- see common.py's load_pft_type_series for why. Fixed 2026-09-15.
    area2d = ds["area"].values
    ixy = ds["pfts1d_ixy"].values.astype(int) - 1
    jxy = ds["pfts1d_jxy"].values.astype(int) - 1
    wt = wt_frac * area2d[jxy, ixy]
    btran = ds["BTRAN"].values          # (12, pft)
    tlai = ds["TLAI"].values            # (12, pft)

    print(f"{res} SSP3-7.0 Default, year {year} -- monthly PFT-weighted means\n")
    print("BTRAN: soil-water stress factor, 1 = no water limitation, 0 = fully stressed")
    print("Domain-mean BTRAN alone does not test local water, cold or daylength triggers.\n")

    for t in [1, 7, 9, 10, 13, 14, 15]:
        m = (itype == t) & (wt > 0)
        if m.sum() == 0:
            continue
        w = wt[m]
        b = np.nansum(btran[:, m] * w, axis=1) / w.sum()
        l = np.nansum(tlai[:, m] * w, axis=1) / w.sum()
        print(f"{t:2d} {PFT_NAMES[t]:15s} [{PHENOLOGY[t]:12s}]")
        print("    BTRAN: " + " ".join(f"{v:5.2f}" for v in b) + f"   min={b.min():.2f}")
        print("    TLAI : " + " ".join(f"{v:5.2f}" for v in l) + f"   min={l.min():.2f}")

    print("\nInterpretation guide:")
    print("  - These domain-mean BTRAN/TLAI values are a screening diagnostic.")
    print("    They do not prove that local phenology criteria were never crossed")
    print("    or establish GPP bias. See ../CRIT_DAYL_STRESS_ARTIFACT.md for")
    print("    the daylength mechanism and newer paired sensitivity results.")
    print("  - Compare TLAI minima: BDT_temp (season_decid) should hit ~0; the")
    print("    stress_decid PFTs are the ones to check.")
    ds.close()


if __name__ == "__main__":
    main()
