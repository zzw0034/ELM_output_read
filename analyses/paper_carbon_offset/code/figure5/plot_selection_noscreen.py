"""
Companion to the main Figure 5 (plot_priority_maps.py): the 4 km siting when risk is ignored. RF, SSP3-7.0,
2091-2100, ranked by the benefit WITHOUT fire loss (same definition as Figure 5 a), 20 % of eligible land.

  a  unscreened selection (top BUDGET % by benefit), coloured by the risk of the selected land: low risk / above
     the fire threshold / above the water-stress threshold only
  b  unscreened vs screened selection (Figure 5 d): selected in both / only without the screen (removed by the
     screen) / only with the screen (land that replaces it)
Thresholds, eligible land and the selection are identical to plot_priority_maps.py.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_selection_noscreen.py [--budget 20 --pct 80]
Output: figures/figure5/fig5_selection_noscreen_<SSP>_<window>.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_selection as ps  # noqa: E402
import plot_priority_maps as pm  # noqa: E402

A_COLS = ["#d9d7d0", "#3987e5", "#e34948", "#008300"]   # not selected, selected & high water only, selected & high fire, selected & low risk
A_NAMES = ["Eligible, not selected", "Selected, high water stress", "Selected, high fire risk", "Selected, low risk"]
B_COLS = ["#d9d7d0", "#eda100", "#e34948", "#008300"]   # neither, only with screen (replacement), only without screen (removed), both
B_NAMES = ["Not selected in either", "Added by the screen (replacement land)", "Removed by the screen", "Selected with and without the screen"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--pct", type=float, default=80)
    ap.add_argument("--budget", type=float, default=20)
    ap.add_argument("--cache-4km", default=os.path.join(ps.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ps.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ps.ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ps.ROOT, "figures/figure5"))
    a = ap.parse_args()
    m = ps.build(a)
    fc = {k: ps.load(os.path.join(a.risk_cache, "4km", f"{a.ssp}{s}__firecum_2024-2100.npz")) for k, s in (("Def", ""), ("RF", "_RF"))}
    dfire = (fc["RF"]["fire_cum_endmean"].astype("f8") - fc["Def"]["fire_cum_endmean"].astype("f8")) * 0.01
    ok = m["ok4"] & np.isfinite(dfire)
    a4 = np.where(ok, m["a4"], 0.0)
    e4 = np.where(ok, m["e4"], 1.0)
    b_nf = np.where(ok, (m["g4"] + dfire) / e4, np.nan)
    E = float(a4.sum())
    T = {k: ps.wquantile(m["R4"][k][ok], a4[ok], a.pct / 100) for k in ("fire", "water")}
    hi_f, hi_w = m["R4"]["fire"] > T["fire"], m["R4"]["water"] > T["water"]
    budget = a.budget / 100 * E
    wU, _ = pm.take_mask(b_nf, a4, ok, budget)
    wS, _ = pm.take_mask(b_nf, a4, ok & ~hi_f & ~hi_w, budget)
    U, S = wU > 0, wS > 0

    clsA = np.where(U, np.where(hi_f, 2, np.where(hi_w, 1, 3)), 0).astype("f8")
    clsA = np.where(ok, clsA, np.nan)
    clsB = np.where(U & S, 3, np.where(U, 2, np.where(S, 1, 0))).astype("f8")
    clsB = np.where(ok, clsB, np.nan)
    shA = {k: 100 * a4[ok & (clsA == k)].sum() / E for k in range(4)}
    shB = {k: 100 * a4[ok & (clsB == k)].sum() / E for k in range(4)}
    G = lambda w: float((w * a4 * np.nan_to_num(b_nf)).sum()) * 100 / 1e9
    selU = float((wU * a4).sum())
    fracf = float((wU * a4 * hi_f).sum() / selU)
    fracw = float((wU * a4 * (hi_w & ~hi_f)).sum() / selU)
    mean_b = lambda s: float(np.average(b_nf[s & ok], weights=a4[s & ok]))
    print(f"unscreened top {a.budget:g}%: captured {G(wU):.3f} PgC (benefit without fire loss); of its area {100 * fracf:.1f}% above the fire "
          f"threshold, {100 * fracw:.1f}% above the water threshold only, {100 * (1 - fracf - fracw):.1f}% low risk")
    print(f"screened: captured {G(wS):.3f} PgC ({100 * (1 - G(wS) / G(wU)):.1f}% less); removed by the screen {shB[2]:.1f}% of eligible land "
          f"(mean benefit {mean_b(U & ~S):.1f} MgC/ha), replacement land {shB[1]:.1f}% (mean benefit {mean_b(S & ~U):.1f} MgC/ha)")

    import cartopy.crs as ccrs
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~ok, 1.0, np.nan)
    fig = plt.figure(figsize=(15.5, 7.6), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(1, 2, wspace=0.08, left=0.04, right=0.985, top=0.88, bottom=0.17)
    for k, (cls, cols, names, sh, ttl) in enumerate((
            (clsA, A_COLS, A_NAMES, shA, f"a  Top {a.budget:g}% benefit without a risk screen"),
            (clsB, B_COLS, B_NAMES, shB, "b  What the fire and water-stress screen changes"))):
        ax = fig.add_subplot(gs[0, k], projection=ccrs.PlateCarree())
        pm.base_map(ax, lon4, lat4)
        pm.mesh(ax, lon4, lat4, inel, ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
        pm.mesh(ax, lon4, lat4, cls, ListedColormap(cols), Normalize(-0.5, 3.5))
        ax.set_title(ttl, loc="left", fontsize=11.5, color=ps.INK, fontweight="bold")
        handles = [plt.Rectangle((0, 0), 1, 1, color=cols[j]) for j in (3, 2, 1, 0)]
        ax.legend(handles, [f"{names[j]} ({sh[j]:.1f}%)" for j in (3, 2, 1, 0)], loc="lower left", fontsize=8.4, framealpha=0.93,
                  edgecolor="none", title="share of eligible land", title_fontsize=8)
    fig.suptitle(f"Siting by the RF benefit without fire loss, with and without the risk screen ({a.ssp}, {a.years}, 4 km)", fontsize=13,
                 color=ps.INK, x=0.04, ha="left", y=0.975)
    fig.text(0.04, 0.015,
             f"Benefit = TOTECOSYSC stock difference RF − Default plus the cumulative fire-loss difference since 2024, per eligible ha (as Figure 5 a). Both "
             f"selections cover {a.budget:g}% of the eligible land.\n"
             f"Risk thresholds = area-weighted p{a.pct:g} of the 4 km fire risk ({T['fire']:.3g} %/yr) and water stress ({T['water']:.3g}) over eligible land. "
             f"Unscreened: {G(wU):.2f} PgC captured, {100 * fracf:.0f}% of the selected land above the fire threshold, {100 * fracw:.0f}% above the "
             f"water threshold only.\nScreened (Figure 5 d): {G(wS):.2f} PgC; the removed land (red in b) is replaced by the next-best low-risk land (yellow).",
             fontsize=8.6, color=ps.INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, f"fig5_selection_noscreen_{a.ssp}_{a.years}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
