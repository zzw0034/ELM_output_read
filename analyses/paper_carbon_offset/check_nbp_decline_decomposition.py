"""
Diagnose why mean future SEUS NBP is lower than the model's 2014-2023 mean.
This script separates a persistent change in NEP / land-use flux from fire
losses and identifies whether a few event years dominate the full-period
mean.

ELM's own accounting (verified from variable long_names in h0):
  NEP = net ecosystem production, EXCLUDES fire/landuse/harvest, +ve = sink
  NBP = net biome production,     INCLUDES fire/landuse/harvest, +ve = sink
The source-exact identity for this ELM version is:
  NBP = NEP - COL_FIRE_CLOSS - LAND_USE_FLUX
  LAND_USE_FLUX = land-cover conversion loss + wood-product-pool loss

COL_FIRE_CLOSS was not saved in these h0 files. PFT_FIRE_CLOSS contains the
patch-level fire loss but omits litter/CWD fire loss. Recover the complete
column fire term from the exact identity:
  implied_COL_FIRE_CLOSS = NEP - LAND_USE_FLUX - NBP
  implied_DECOMP_FIRE_CLOSS = implied_COL_FIRE_CLOSS - PFT_FIRE_CLOSS

The implied terms close the budget by construction and therefore are not an
independent validation. A targeted run that outputs COL_FIRE_CLOSS is needed
for that. See NBP_RESIDUAL_REVIEW_20260915.md.

Variables used:
  NEP                       gC/m2/s, native
  NBP                       gC/m2/s, native
  PFT_FIRE_CLOSS            gC/m2/s, fire loss
  LAND_USE_FLUX             gC/m2/s, conversion plus product-pool loss

Usage: python check_nbp_decline_decomposition.py [0.5deg|4km]
"""
import sys

import numpy as np
import xarray as xr

from common import (HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR,
                    SEC_PER_YEAR_NOLEAP, h0_files, year_of, area_weights,
                    day_weighted_annual_mean, domain_total_PgC)

VARS = ["NEP", "NBP", "PFT_FIRE_CLOSS", "LAND_USE_FLUX"]

WINDOWS = [
    (2024, 2043),
    (2044, 2063),
    (2064, 2083),
    (2084, 2100),
]


def load(case, subdir, year_min=None):
    files = h0_files(case, subdir)
    if year_min is not None:
        files = [f for f in files if year_of(f) >= year_min]
    out = {"year": []}
    for v in VARS:
        out[v + "_PgC"] = []
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        w = area_weights(ds)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        out["year"].append(year_of(f))
        for v in VARS:
            vals = day_weighted_annual_mean(ds[v], tb) * SEC_PER_YEAR_NOLEAP
            out[v + "_PgC"].append(domain_total_PgC(vals, w))
        ds.close()
    return {k: np.array(v) for k, v in out.items()}


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else "0.5deg"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)

    print(f"Loading transient tail (2014-2023) ...")
    hist = load(cases["transient"], subdir, year_min=2014)

    scenarios = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5",
                 "SSP3-7.0 RF", "SSP3-7.0 DF", "SSP3-7.0 RH"]
    fut = {}
    for s in scenarios:
        print(f"Loading {s} ({cases[s]}) ...")
        fut[s] = load(cases[s], subdir)

    def summarize(label, d, mask):
        nep = np.nanmean(d["NEP_PgC"][mask])
        fire = np.nanmean(d["PFT_FIRE_CLOSS_PgC"][mask])
        land_use_flux = np.nanmean(d["LAND_USE_FLUX_PgC"][mask])
        nbp_native = np.nanmean(d["NBP_PgC"][mask])
        col_fire = nep - land_use_flux - nbp_native
        decomp_fire = col_fire - fire
        return dict(label=label, NEP=nep, fire=fire,
                    land_use_flux=land_use_flux, NBP_native=nbp_native,
                    col_fire=col_fire, decomp_fire=decomp_fire)

    rows = [summarize("historical 2014-2023", hist, hist["year"] >= 2014)]
    for s in scenarios:
        rows.append(summarize(s, fut[s], np.ones_like(fut[s]["year"], dtype=bool)))

    print(f"\n--- Source-exact NBP decomposition, mean annual domain totals (PgC/yr), {res} ---")
    print(f"{'':24s} {'NEP':>8} {'-PFTfire':>10} {'-decompfire':>12} "
          f"{'-fullfire':>10} {'-LUflux':>10} {'NBP':>9}")
    for r in rows:
        print(f"{r['label']:24s} {r['NEP']:8.4f} {-r['fire']:10.4f} "
              f"{-r['decomp_fire']:12.4f} {-r['col_fire']:10.4f} "
              f"{-r['land_use_flux']:10.4f} {r['NBP_native']:9.4f}")

    print("\n--- What explains each scenario's mean NBP difference from 2014-2023? ---")
    h = rows[0]
    print(f"(historical NBP = {h['NBP_native']:.4f} PgC/yr)")
    print(f"{'scenario':16s} {'NBP gap':>10} {'dNEP':>9} {'dFullFire':>11} "
          f"{'dLUflux':>10} {'%NEP':>8} {'%fire':>8} {'%LU':>8}")
    for r in rows[1:]:
        gap = h["NBP_native"] - r["NBP_native"]
        dNEP = h["NEP"] - r["NEP"]
        dFire = r["col_fire"] - h["col_fire"]
        dLuf = r["land_use_flux"] - h["land_use_flux"]
        denom = gap if abs(gap) > 1e-6 else np.nan
        print(f"{r['label']:16s} {gap:10.4f} {dNEP:9.4f} {dFire:11.4f} {dLuf:10.4f} "
              f"{100*dNEP/denom:7.1f}% {100*dFire/denom:7.1f}% "
              f"{100*dLuf/denom:7.1f}%")

    print("\n--- Four future periods: is lower NBP gradual or event-driven? (PgC/yr) ---")
    print(f"{'scenario / years':29s} {'NEP':>8} {'full fire':>10} {'LU flux':>9} {'NBP':>9}")
    for s in scenarios:
        d = fut[s]
        implied_col_fire = d["NEP_PgC"] - d["LAND_USE_FLUX_PgC"] - d["NBP_PgC"]
        for y0, y1 in WINDOWS:
            m = (d["year"] >= y0) & (d["year"] <= y1)
            print(f"{s + ' ' + str(y0) + '-' + str(y1):29s} "
                  f"{np.nanmean(d['NEP_PgC'][m]):8.4f} "
                  f"{np.nanmean(implied_col_fire[m]):10.4f} "
                  f"{np.nanmean(d['LAND_USE_FLUX_PgC'][m]):9.4f} "
                  f"{np.nanmean(d['NBP_PgC'][m]):9.4f}")

    print("\n--- Cumulative 2024-2100 accounting (PgC) ---")
    print(f"{'scenario':16s} {'sum NEP':>10} {'sum fire':>10} {'sum LU':>9} "
          f"{'sum NBP':>10} {'NBP no fire':>12}")
    for s in scenarios:
        d = fut[s]
        implied_col_fire = d["NEP_PgC"] - d["LAND_USE_FLUX_PgC"] - d["NBP_PgC"]
        print(f"{s:16s} {np.nansum(d['NEP_PgC']):10.3f} "
              f"{np.nansum(implied_col_fire):10.3f} "
              f"{np.nansum(d['LAND_USE_FLUX_PgC']):9.3f} "
              f"{np.nansum(d['NBP_PgC']):10.3f} "
              f"{np.nansum(d['NEP_PgC'] - d['LAND_USE_FLUX_PgC']):12.3f}")

    print("\n--- Five largest full-column fire-loss years per scenario ---")
    for s in scenarios:
        d = fut[s]
        implied_col_fire = d["NEP_PgC"] - d["LAND_USE_FLUX_PgC"] - d["NBP_PgC"]
        order = np.argsort(np.nan_to_num(implied_col_fire, nan=-np.inf))[-5:][::-1]
        events = ", ".join(
            f"{int(d['year'][i])}: fire={implied_col_fire[i]:.3f}, NBP={d['NBP_PgC'][i]:+.3f}"
            for i in order
        )
        print(f"  {s}: {events}")


if __name__ == "__main__":
    main()
