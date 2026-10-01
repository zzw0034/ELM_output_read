"""
Diagnostic for the Figure 4 strata: benefit versus the size of RF's land-cover
increment, in bins of increment (tree fraction of the cell, RF plateau year minus
transient 2023). A continuous version of the restoration / protection-only split,
because the threshold strata of plot_pool_strata.py put 69 % of the land (939 x10^3
km2 at the 0.01 threshold) in "restoration": the increment is thin and widespread,
not concentrated (73 % of land has an increment > 0.001, mean 0.14 of the cell).

Per bin (area x landfrac weighted): area, RF - Default and RH - Default TOTECOSYSC
and RF - Default TOTSOMC (MgC/ha of land), and the Default wood harvest. Reading:
the lowest bin (no RF land-cover change) is the harvest-ban effect alone, plus any
drift between RF and Default land use; the rise of the benefit with the increment is
the restoration contribution.

Runs locally from the analysis root, after plot_pool_strata.py's inputs are in place:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure4/check_increment_dose_response.py [SSP3-7.0]
Inputs: _cache/figure4/4km/<SSP>[_RF|_RH]__pools_2091-2100.npz,
        transient__treefrac_2023.npz, <SSP>_RF__treefrac_2060.npz
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CD = os.path.join(ROOT, "_cache/figure4/4km")
BINS = [(-1, 1e-3), (1e-3, 0.01), (0.01, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.01)]


def main():
    ssp = sys.argv[1] if len(sys.argv) > 1 else "SSP3-7.0"
    c = lambda t: np.load(os.path.join(CD, f"{t}.npz"))
    D, RF, RH = (c(f"{ssp}{s}__pools_2091-2100") for s in ("", "_RF", "_RH"))
    base, rf = c("transient__treefrac_2023"), c(f"{ssp}_RF__treefrac_2060")
    for z in (RF, RH, base, rf):
        assert np.array_equal(z["area_km2"], D["area_km2"]), "grid differs"
    A = D["area_km2"].astype("f8")
    f = lambda x: x.astype("f8")
    inc = f(rf["tree_frac"]) - f(base["tree_frac"])
    m = (A > 0) & np.isfinite(inc)
    dT = f(RF["TOTECOSYSC"]) - f(D["TOTECOSYSC"])
    dH = f(RH["TOTECOSYSC"]) - f(D["TOTECOSYSC"])
    dS = f(RF["TOTSOMC"]) - f(D["TOTSOMC"])
    harv = f(D["WOOD_HARVESTC"])
    sel = m & (inc > 1e-3)
    print(f"{ssp}: land with increment > 0.001: {100 * A[sel].sum() / A[m].sum():.1f}% of area, "
          f"mean increment there {np.average(inc[sel], weights=A[sel]):.3f}")
    print(f"{'increment bin':16s}{'area 1e3km2':>12s}{'dTOT MgC/ha':>12s}{'RH MgC/ha':>11s}{'dSOC MgC/ha':>12s}{'harvest gC/m2/yr':>18s}")
    tot_area = 0.0
    for lo, hi in BINS:
        s = m & (inc <= hi) if lo < 0 else m & (inc > lo) & (inc <= hi)
        w = A[s]
        if w.sum() == 0:
            continue
        tot_area += w.sum()
        g = lambda x: np.average(x[s], weights=w) * 0.01  # gC/m2 -> MgC/ha
        print(f"{f'({lo:g},{hi:g}]':16s}{w.sum() / 1e3:12.1f}{g(dT):12.1f}{g(dH):11.1f}{g(dS):12.2f}{np.average(harv[s], weights=w):18.2f}")
    assert abs(tot_area - A[m].sum()) < 1e-6 * A[m].sum(), "bins do not cover the valid area"


if __name__ == "__main__":
    main()
