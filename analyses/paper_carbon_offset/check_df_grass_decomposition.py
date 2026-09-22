"""
Legacy partial-pool decomposition of the idealized Default-DF stock benefit.

Supporting diagnostic for new Main Figure 4 / the supplement. Vegetation
includes grass leaves and roots, so its dominance does not prove immunity
to phenology bias. A positive DF-minus-Default SOC response does not establish
a conservative bias relative to observations. Any pool residual is unassigned
until checked against the actual model definitions.

This is not a sensitivity rerun. Newer source/parameter diagnostics and
paired 0.5-degree Default/DF runs at crit_dayl_stress=38000 s are documented
in ../CRIT_DAYL_STRESS_ARTIFACT.md and DF_GRASS_SENSITIVITY.md.

Usage inside an approved Slurm allocation:
    python check_df_grass_decomposition.py [0.5deg|4km]
"""
import sys

import numpy as np

from common import HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, load_annual_series

VEG_VARS = ["TOTVEGC"]
DEAD_VARS = ["TOTSOMC", "TOTLITC", "CWDC"]
ALL_VARS = ["TOTECOSYSC"] + VEG_VARS + DEAD_VARS


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else "0.5deg"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)

    print(f"Resolution: {res}")
    print(f"Loading Default (SSP3-7.0): {cases['SSP3-7.0']}")
    default = load_annual_series(cases["SSP3-7.0"], ALL_VARS, subdir=subdir)
    print(f"Loading DF: {cases['SSP3-7.0 DF']}")
    df = load_annual_series(cases["SSP3-7.0 DF"], ALL_VARS, subdir=subdir)

    year = default["year"]
    assert np.array_equal(year, df["year"]), "year axes differ"

    # Proposal Table 2 sign convention for forest preservation: Default - DF.
    offset_total = default["TOTECOSYSC_PgC"] - df["TOTECOSYSC_PgC"]
    veg_term = default["TOTVEGC_PgC"] - df["TOTVEGC_PgC"]
    dead_term = sum((default[v + "_PgC"] - df[v + "_PgC"]) for v in DEAD_VARS)

    print("\n--- Decomposition of the avoided-deforestation offset (Default - DF) ---")
    print(f"{'year':>6} {'total':>10} {'veg':>10} {'soil+lit+cwd':>14} {'veg share':>10}")
    for yr in [2024, 2050, 2075, 2100]:
        if yr not in year:
            continue
        i = int(np.where(year == yr)[0][0])
        share = 100 * veg_term[i] / offset_total[i] if offset_total[i] != 0 else np.nan
        print(f"{yr:6d} {offset_total[i]:10.3f} {veg_term[i]:10.3f} {dead_term[i]:14.3f} {share:9.1f}%")

    end = year >= 2091
    tot_end = float(np.nanmean(offset_total[end]))
    veg_end = float(np.nanmean(veg_term[end]))
    dead_end = float(np.nanmean(dead_term[end]))
    print(f"\n2091-2100 mean: total={tot_end:.3f} PgC, veg={veg_end:.3f} PgC "
          f"({100*veg_end/tot_end:.1f}%), soil+litter+cwd={dead_end:.3f} PgC "
          f"({100*dead_end/tot_end:.1f}%)")

    # Cross-check: native TOTECOSYSC vs the sum of its parts.
    parts = default["TOTVEGC_PgC"] + sum(default[v + "_PgC"] for v in DEAD_VARS)
    resid = default["TOTECOSYSC_PgC"] - parts
    print(f"\nSanity check (Default): native TOTECOSYSC minus (TOTVEGC+TOTSOMC+TOTLITC+CWDC)")
    print(f"  mean residual {np.nanmean(resid):.4f} PgC ({100*np.nanmean(resid)/np.nanmean(default['TOTECOSYSC_PgC']):.2f}% of total)")
    print("  Unassigned residual: verify pool definitions and spatial normalization")
    print("  in the actual model version before attributing it to specific pools.")

    # Direction of the soil-carbon response to deforestation.
    soc_diff = df["TOTSOMC_PgC"] - default["TOTSOMC_PgC"]
    print(f"\n--- Soil carbon: DF minus Default (positive = deforested run holds MORE soil C) ---")
    for yr in [2024, 2050, 2100]:
        if yr not in year:
            continue
        i = int(np.where(year == yr)[0][0])
        print(f"  {yr}: {soc_diff[i]:+.3f} PgC")
    trend = np.polyfit(year, soc_diff, 1)[0] * 100
    print(f"  trend: {trend:+.4f} PgC/century")
    if np.nanmean(soc_diff[end]) > 0:
        print("  NOTE: positive DF-minus-Default SOC is a modeled response, not proof")
        print("  of a signed bias relative to observations. See DF_GRASS_SENSITIVITY.md")
        print("  for the newer paired parameter sensitivity and its limits.")


if __name__ == "__main__":
    main()
