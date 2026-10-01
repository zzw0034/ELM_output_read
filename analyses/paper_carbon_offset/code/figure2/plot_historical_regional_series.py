"""
Figure 2, first panel set: historical regional series of the SEUS domain from the
ELM 4 km transient run, yearly (results only, no 0.5 deg comparison since 2026-10-01):
  (a) forest area (tree-PFT area, itype 1-8)           [10^3 km2]
  (b) regional GPP                                       [PgC / yr]
  (c) soil organic carbon, change relative to the first year [PgC]
  (d) regional NBP (positive = sink, includes fire, land use and harvest) [PgC / yr]

Inputs (pulled from Pathfinder `_cache/figure2/` into the local `_cache/figure2/`):
  transient_domain_totals_4km.npz   from extract_domain_totals.py
  transient_forest_area_4km.npz     from extract_forest_area.py
SOC = TOTSOMC (soil organic matter pools only, full profile; litter and CWD
excluded), shown as a change since the first year.

Colour: categorical slot 1 of the dataviz reference palette (blue); one series per
panel, so no legend; one y-axis per panel.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \
        code/figure2/plot_historical_regional_series.py [year_min year_max]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root
CACHE = os.path.join(ROOT, "_cache/figure2")
OUT_DIR = os.path.join(ROOT, "figures/figure2")
RES = {"4km": ("ELM 4 km", "#2a78d6", "-")}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load(res):
    t = np.load(os.path.join(CACHE, f"transient_domain_totals_{res}.npz"))
    f = np.load(os.path.join(CACHE, f"transient_forest_area_{res}.npz"))
    assert np.array_equal(t["year"], f["year"]), f"{res}: h0 and h1 years differ"
    return t, f


def main():
    data = {r: load(r) for r in RES}
    years = data["4km"][0]["year"]
    y0 = int(sys.argv[1]) if len(sys.argv) > 1 else int(years[0])
    y1 = int(sys.argv[2]) if len(sys.argv) > 2 else int(years[-1])
    sel = (years >= y0) & (years <= y1)
    yr = years[sel]

    panels = [
        ("(a) Forest area (tree PFTs)", "10$^3$ km$^2$", lambda t, f: f["tree_area_km2"] / 1e3, False),
        ("(b) Gross primary production", "PgC yr$^{-1}$", lambda t, f: t["GPP"], False),
        (f"(c) Soil organic carbon, change since {y0}", "PgC", lambda t, f: t["TOTSOMC"] - t["TOTSOMC"][sel][0], False),
        ("(d) Net biome production (positive = sink)", "PgC yr$^{-1}$", lambda t, f: t["NBP"], True),
    ]
    plt.rcParams.update({"font.size": 11, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.edgecolor": GRID})
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.2), sharex=True)
    print(f"years {y0}-{y1}")
    for ax, (title, ylab, fn, zero) in zip(axes.ravel(), panels):
        for res, (label, color, ls) in RES.items():
            t, f = data[res]
            y = fn(t, f)[sel]
            ax.plot(yr, y, color=color, ls=ls, lw=1.8, label=label)
            print(f"  {title[:28]:<28s} {label:<9s} {y[0]:9.3f} -> {y[-1]:9.3f}  (min {y.min():.3f}, max {y.max():.3f})")
        if zero:
            ax.axhline(0, color=INK2, lw=0.8)
        ax.set_title(title, loc="left", fontsize=11.5, color=INK)
        ax.set_ylabel(ylab)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.set_xlim(yr[0], yr[-1])
    for ax in axes[1]:
        ax.set_xlabel("year")
    fig.suptitle(f"Southeastern U.S., ELM 4 km historical simulation {y0}–{y1}: regional totals", x=0.06, ha="left",
                 fontsize=13, y=0.995)
    fig.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"hist_regional_series_{y0}-{y1}.png")
    fig.savefig(out, dpi=200, facecolor="white")
    print(f"Saved {out}")

    print("\nChecks")
    for res, (label, _, _) in RES.items():
        t, f = data[res]
        print(f"  {label}: land area {t['land_area_km2'][0] / 1e6:.4f} Mkm2; PFT area / land area "
              f"{f['pft_area_ratio'].min():.4f}-{f['pft_area_ratio'].max():.4f}; "
              f"TOTSOMC first year {t['TOTSOMC'][0]:.2f} PgC; product residual {t['prod_resid'][0]:+.4f} -> {t['prod_resid'][-1]:+.4f} PgC; "
              f"cumulative NBP {np.nansum(t['NBP'][sel]):+.2f} PgC vs d(TOTECOSYSC) {t['TOTECOSYSC'][sel][-1] - t['TOTECOSYSC'][sel][0]:+.2f} PgC")


if __name__ == "__main__":
    main()
