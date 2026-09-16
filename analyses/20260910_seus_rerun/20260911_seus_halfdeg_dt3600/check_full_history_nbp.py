"""
Quick check: what does the TRANSIENT case's full 1850-2023 cumulative NBP
look like, in magnitude, vs. the 2014-2023 "tail" already used elsewhere
in this folder's plots? Informs whether Panel A of
future_scenario_cumulative_nbp_split.png should show the full historical
record instead of just the last decade.

Runs on Pathfinder via Slurm (submit_py.sbatch).
"""
import numpy as np

from common import TRANSIENT, load_annual_domain_series

VARS = ["NBP"]


def main():
    hist = load_annual_domain_series(TRANSIENT, VARS)
    years = hist["year"]
    print(f"TRANSIENT case: {TRANSIENT}")
    print(f"Years available: {years.min()}-{years.max()} ({years.size} yr)\n")

    cum_full = np.cumsum(np.nan_to_num(hist["NBP_domaintotal"]))
    print(f"Full 1850-{years.max()} cumulative NBP: {cum_full[-1]:+.3f} PgC")
    print(f"  min along the way: {cum_full.min():+.3f} PgC "
          f"(year {years[np.argmin(cum_full)]})")
    print(f"  max along the way: {cum_full.max():+.3f} PgC "
          f"(year {years[np.argmax(cum_full)]})")

    tail = years >= 2014
    cum_tail = np.cumsum(np.nan_to_num(hist["NBP_domaintotal"][tail]))
    print(f"\n2014-{years.max()} cumulative NBP (the current 'tail' window): "
          f"{cum_tail[-1]:+.3f} PgC")

    # A few decadal checkpoints for context.
    for yr in [1850, 1900, 1950, 1980, 2000, 2010, 2014, 2020, 2023]:
        idx = np.searchsorted(years, yr)
        if idx < years.size and years[idx] == yr:
            print(f"  cumulative through {yr}: {cum_full[idx]:+.3f} PgC")


if __name__ == "__main__":
    main()
