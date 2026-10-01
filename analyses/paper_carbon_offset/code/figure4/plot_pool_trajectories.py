"""
Figure 4 companion: the pool contributions to RF - Default and RH - Default over the
whole future, 2024-2100, as domain totals (PgC), 4 km, one SSP. plot_pool_strata.py
shows only the 2091-2100 mean, which is the end state; this shows when each pool
moves (products fall at once while vegetation accumulates for decades; SOC declines
for ~50 years and partly recovers).

Source: the annual domain totals of extract_domain_totals.py (notes 3.6),
_cache/figure2/future_4km/<SSP>[_RF|_RH]__totals.npz. Pools as in plot_pool_strata.py:
aboveground vegetation = TOTVEGC_ABG, other vegetation = TOTVEGC - TOTVEGC_ABG, CWDC,
TOTLITC, TOTSOMC (full column, see notes 3.12), wood products = TOTECOSYSC -
(TOTVEGC + CWDC + TOTLITC + TOTSOMC). The six pools add up to the black total line.
Each panel has its own y axis (RH is ~5x smaller); RF = restoration plus a harvest ban.

Runs locally from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure4/plot_pool_trajectories.py [SSP3-7.0]
Output: figures/figure4/fig4_pool_trajectories_4km_<SSP>.png and a CSV.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "_cache/figure2/future_4km")
OUT = os.path.join(ROOT, "figures/figure4")
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e9e8e4", "#fcfcfb"
POOLS = [("abg", "Aboveground veg.", "#1baf7a"), ("veg_other", "Other veg.", "#eda100"),
         ("cwd", "CWD", "#e87ba4"), ("lit", "Litter", "#008300"), ("soc", "SOC", "#4a3aa7"),
         ("prod", "Products", "#e34948")]


def pools(x):
    prod = x["TOTECOSYSC"] - (x["TOTVEGC"] + x["CWDC"] + x["TOTLITC"] + x["TOTSOMC"])
    return {"abg": x["TOTVEGC_ABG"], "veg_other": x["TOTVEGC"] - x["TOTVEGC_ABG"], "cwd": x["CWDC"],
            "lit": x["TOTLITC"], "soc": x["TOTSOMC"], "prod": prod}


def spread(ys, gap):
    order = np.argsort(ys)
    out = np.array(ys, float)
    for a, b in zip(order[:-1], order[1:]):
        if out[b] - out[a] < gap:
            out[b] = out[a] + gap
    return out


def main():
    ssp = sys.argv[1] if len(sys.argv) > 1 else "SSP3-7.0"
    c = lambda s: np.load(os.path.join(CACHE, f"{ssp}{s}__totals.npz"), allow_pickle=True)
    D, runs = c(""), {"RF": c("_RF"), "RH": c("_RH")}
    yr = D["year"]
    for r in runs.values():
        assert np.array_equal(r["year"], yr), "year axes differ"
    PD = pools(D)
    os.makedirs(OUT, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), facecolor=SURFACE)
    rows = []
    for ax, (nm, R) in zip(axes, runs.items()):
        PR = pools(R)
        delta = {k: PR[k] - PD[k] for k, _, _ in POOLS}
        total = R["TOTECOSYSC"] - D["TOTECOSYSC"]
        assert np.allclose(sum(delta.values()), total, atol=1e-9), "pools do not add up to TOTECOSYSC"
        for k, label, col in POOLS:
            ax.plot(yr, delta[k], color=col, lw=2)
        ax.plot(yr, total, color="black", lw=2.6)
        ends = [delta[k][-1] for k, _, _ in POOLS] + [total[-1]]
        span = max(abs(max(ends)), abs(min(ends)), 1e-6)
        ly = spread(ends, span * 0.07)
        for (lab, col), y0, y1 in zip([(l, c_) for _, l, c_ in POOLS] + [("Total", "black")], ends, ly):
            ax.text(2101.5, y1, lab, color=INK2, fontsize=9, va="center")
        ax.axhline(0, color="black", lw=0.9)
        ax.set_xlim(2024, 2100)
        ax.set_title(f"{nm} − Default  ({ssp}, 4 km)", loc="left", fontsize=11.5, fontweight="bold", color=INK)
        ax.set_ylabel("Domain total difference (PgC)", fontsize=10.5, color=INK)
        ax.grid(axis="y", color=GRID, lw=0.9)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=9.5)
        for k in [p[0] for p in POOLS] + ["total"]:
            d = total if k == "total" else delta[k]
            for y, v in zip(yr, d):
                rows.append([nm, k, int(y), f"{v:.5f}"])
    fig.subplots_adjust(left=0.07, right=0.89, wspace=0.38, top=0.9, bottom=0.2)
    fig.suptitle("When each pool moves: pool contributions to the management benefit, 2024–2100", x=0.07, ha="left",
                 fontsize=13, color=INK)
    fig.text(0.07, 0.03, "Domain totals, area × landfrac weighted; the six pools add up to the black total (TOTECOSYSC difference). "
             "Products derived as TOTECOSYSC − (TOTVEGC + CWDC + TOTLITC + TOTSOMC).\n"
             "SOC = full soil column (TOTSOMC). RF = restoration plus a region-wide harvest ban. Each panel has its own y axis.",
             fontsize=8.6, color=INK2)
    png = os.path.join(OUT, f"fig4_pool_trajectories_4km_{ssp}.png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    with open(os.path.join(OUT, f"fig4_pool_trajectories_4km_{ssp}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["mgmt", "pool", "year", "diff_vs_Default_PgC"])
        w.writerows(rows)
    print("wrote", png)


if __name__ == "__main__":
    main()
